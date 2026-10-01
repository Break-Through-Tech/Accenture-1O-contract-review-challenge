import unicodedata
import re
import pandas as pd
from sklearn.metrics import f1_score, recall_score


class KeywordClassifier:
    def __init__(self, scorecards):
        self.scorecards = scorecards

    @staticmethod
    def normalize_text(text, return_mapping=False):
        """
        Applies normalization for keyword matching in the following order:
            - Unicode NFKC normalization;
            - Unicode case-folding;
            - consistent equivalents for typographic quotation marks and dashes; and
            - replacement of each whitespace run with one space.

        :param text: Source text to normalize.
        :param return_mapping: Whether to return a mapping from normalized text
            positions to positions in the original text.
        :return: Normalized text, or a tuple of normalized text and position mapping
            when return_mapping is True.
        """
        normalized = []
        mapping = []

        for i, char in enumerate(text):
            # Unicode NFKC normalization and case-folding
            char = unicodedata.normalize("NFKC", char).casefold()

            # consistent equivalents for typographic quotation marks and dashes
            replacements = {
                "\u2018": "'",
                "\u2019": "'",
                "\u201c": '"',
                "\u201d": '"',
                "\u2013": "-",
                "\u2014": "-",
                "\u2212": "-",
            }

            for old, new in replacements.items():
                char = char.replace(old, new)

            for c in char:
                normalized.append(c)
                mapping.append(i)

        # Collapse whitespace runs
        final_text = []
        final_mapping = []
        previous_space = False

        # replacement of each whitespace run with one space
        for char, original_pos in zip(normalized, mapping):
            if char.isspace():
                if previous_space:
                    continue
                char = " "
                previous_space = True
            else:
                previous_space = False

            final_text.append(char)
            final_mapping.append(original_pos)

        normalized_text = "".join(final_text)

        if return_mapping:
            return normalized_text, final_mapping

        return normalized_text

    def find_matches(self, chunk, group):
        """
        Finds occurrences of keyword phrases defined by an evidence group
        :param chunk: A raw chunk from a contract
        :param group: The EvidenceGroup to be matched
        :return: A list of all matching phrases and their metadata including rule_id,
            matched_text, and start and end indices in the raw chunk
        """
        matches = []

        normalized_chunk, mapping = self.normalize_text(
            chunk,
            return_mapping=True
        )

        # for each rule
        for rule in group.rules:
            for phrase in rule.phrases:

                # normalize phrase to keep matching consistent
                norm_phrase = self.normalize_text(phrase).strip()

                # Skip empty/whitespace-only phrases
                if not norm_phrase:
                    continue

                pattern = re.compile(
                    r"(?<!\w)" + re.escape(norm_phrase) + r"(?!\w)"
                )

                # find matching phrases
                for match in pattern.finditer(normalized_chunk):
                    normalized_start = match.start()
                    normalized_end = match.end()

                    # map to original text indices
                    original_start = mapping[normalized_start]
                    original_end = mapping[normalized_end - 1] + 1

                    matches.append({
                        "rule_id": rule.rule_id,
                        "phrase": phrase,
                        "matched_text": match.group(),
                        "start": original_start,
                        "end": original_end,
                    })

        return matches

    def score_chunk(self, chunk, scorecard):
        """
        Score a contract chunk for one core category.

        :param chunk: The contract chunk to be scored.
        :param scorecard: The scorecard defining the evidence groups and rules for the category.
        :return: A dictionary containing the category score and recorded evidence matches used to
            calculate the score.
        """
        groups = (
                scorecard.anchor_groups
                + scorecard.supporting_groups
                + scorecard.counterevidence_groups
                + scorecard.veto_groups
        )

        evidence = []
        veto_flag = False

        # find matches for each evidence group
        for group in groups:
            matches = self.find_matches(chunk, group)

            if matches:
                # if a veto group matches (effect=0), set the final score to 0
                if group.effect.value == 0:
                    veto_flag = True
                evidence.append({
                    "group_id": group.group_id,
                    "effect": group.effect.name,
                    "points": group.effect.value,
                    "matches": matches,
                })

        # calculate the total score
        score = max(0, sum(e["points"] for e in evidence))
        score = 0 if veto_flag else score

        return {
            "category": scorecard.category,
            "score": score,
            "evidence": evidence,
        }

    def score(self, chunks):
        """
        Score each contract chunk for each core category.
        :param chunks: DataFrame containing the contract chunks to score
        :return: DataFrame containing one score and recorded evidence for each chunk-category pair.
        """
        results = []
        for _, row in chunks.iterrows():
            for category, scorecard in self.scorecards.items():
                result = self.score_chunk(row["text"], scorecard)

                results.append({
                    "contract_id": row["contract_id"],
                    "chunk_id": row["chunk_id"],
                    "category_name": category,
                    "score": result["score"],
                    "evidence": result["evidence"],
                })
        return pd.DataFrame(results)

    def select_thresholds(self, evaluation):
        """
        Selects the optimal score threshold for each core category
        :param evaluation: DataFrame containing keyword scores and gold labels for each
            chunk-category pair
        :return: A tuple containing the selected threshold for each category and a DataFrame
            containing the results of all evaluated thresholds
        """
        thresholds = []

        for category, scorecard in self.scorecards.items():
            data = evaluation[evaluation["category_name"] == category]

            # calculate the maximum possible score for the category
            # based on its scorecard's evidence groups
            max_score = sum(
                group.effect.value
                for group in (
                        scorecard.anchor_groups
                        + scorecard.supporting_groups
                        + scorecard.counterevidence_groups
                        + scorecard.veto_groups
                )
                if group.effect.value > 0
            )

            # calculate the f1 score and recall for each threshold
            for threshold in range(1, max_score + 1):
                predictions = (data["score"] >= threshold).astype(int)

                f1 = f1_score(
                    data["gold"],
                    predictions,
                    zero_division=0
                )

                recall = recall_score(
                    data["gold"],
                    predictions,
                    zero_division=0
                )

                thresholds.append({
                    "category_name": category,
                    "threshold": threshold,
                    "f1": f1,
                    "recall": recall
                })

        threshold_results = pd.DataFrame(thresholds)

        # Select the threshold with the highest validation F1.
        # If thresholds have exactly the same F1, select the one with higher recall.
        # If they also have the same recall, select the lower threshold.
        selected = (
            threshold_results
            .sort_values(
                ["category_name", "f1", "recall", "threshold"],
                ascending=[True, False, False, True]
            )
            .groupby("category_name")
            .first()
            .reset_index()
        )

        return selected, threshold_results

    def predict(self, scores, thresholds):
        """
        Generate binary predictions for each chunk-category pair using the
        selected score threshold for each category.

        :param scores: DataFrame containing the score for each chunk-category pair.
        :param thresholds: DataFrame containing the selected threshold for each
           core category.
        :return: DataFrame containing the original scores and a binary prediction
           for each chunk-category pair.
        """
        threshold_map = dict(
            zip(
                thresholds["category_name"],
                thresholds["threshold"]
            )
        )

        predictions = scores.copy()

        predictions["prediction"] = (
                predictions["score"]
                >= predictions["category_name"].map(threshold_map)
        ).astype(int)

        return predictions