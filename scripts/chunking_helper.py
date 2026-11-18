import re
import pandas as pd


def create_paragraph_chunks(
    documents_df,
    tokenizer,
    chunk_size=512,
    long_paragraph_overlap=64,
    method_name="paragraph_based"
):
    """
    Create paragraph-aware chunks.

    Whole paragraphs are grouped together whenever possible without
    exceeding the model's token limit.

    If a single paragraph is longer than the allowed chunk size,
    that paragraph is split into token windows using a small overlap.

    Parameters:
        documents_df:
            Training documents containing contract_id,
            context_group_id, and context.

        tokenizer:
            Tokenizer used for the downstream model.

        chunk_size:
            Maximum model input length, including special tokens.

        long_paragraph_overlap:
            Overlap used only when an individual paragraph is too
            long to fit into one chunk.

        method_name:
            Name used to identify this chunking method.

    Returns:
        DataFrame containing the generated chunks and their
        character boundaries.
    """

    chunk_records = []

    # DistilRoBERTa uses special tokens around each sequence.
    num_special_tokens = tokenizer.num_special_tokens_to_add(
        pair=False
    )

    max_content_tokens = (
        chunk_size - num_special_tokens
    )

    # Process each contract separately.
    for _, row in documents_df.iterrows():

        contract_id = row["contract_id"]
        context_group_id = row["context_group_id"]
        text = str(row["context"])

        # ---------------------------------------------------------
        # Find paragraph-like sections.
        # Paragraphs are treated as blocks separated by one or more
        # blank lines.
        # Using regex the original character positions are preserved in the full contract.
        # ---------------------------------------------------------
        paragraph_matches = list(
            re.finditer(
                r"\S(?:.*?)(?=\n\s*\n|\Z)",
                text,
                flags=re.DOTALL
            )
        )

        chunk_number = 0

        # These variables keep track of paragraphs being grouped together into the current chunk.
        current_start = None
        current_end = None
        current_token_count = 0

        for match in paragraph_matches:

            paragraph_text = match.group(0)

            paragraph_start = match.start()
            paragraph_end = match.end()

            # Tokenize the paragraph without adding model special tokens.
            paragraph_encoding = tokenizer(
                paragraph_text,
                add_special_tokens=False,
                truncation=False,
                return_offsets_mapping=True
            )

            paragraph_tokens = (
                paragraph_encoding["input_ids"]
            )

            paragraph_offsets = (
                paragraph_encoding["offset_mapping"]
            )

            paragraph_token_count = len(
                paragraph_tokens
            )


            # CASE 1:
            # One paragraph is longer than the model limit.
            if paragraph_token_count > max_content_tokens:

                # Save the chunk we were already building before processing the oversized paragraph.
                if current_start is not None:

                    chunk_records.append({
                        "method": method_name,
                        "contract_id": contract_id,
                        "context_group_id": context_group_id,
                        "chunk_id":
                            f"{contract_id}__chunk_{chunk_number:04d}",
                        "chunk_number": chunk_number,
                        "char_start": current_start,
                        "char_end": current_end,
                        "num_tokens":
                            current_token_count
                            + num_special_tokens
                    })

                    chunk_number += 1

                    current_start = None
                    current_end = None
                    current_token_count = 0

                # Split the unusually long paragraph using 512-token windows with a smaller 64-token overlap.
                step = (
                    max_content_tokens
                    - long_paragraph_overlap
                )

                for start_token in range(
                    0,
                    paragraph_token_count,
                    step
                ):

                    end_token = min(
                        start_token + max_content_tokens,
                        paragraph_token_count
                    )

                    piece_offsets = paragraph_offsets[
                        start_token:end_token
                    ]

                    if not piece_offsets:
                        continue

                    # Convert paragraph-relative offsets back to character positions in the full contract.
                    char_start = (
                        paragraph_start
                        + piece_offsets[0][0]
                    )

                    char_end = (
                        paragraph_start
                        + piece_offsets[-1][1]
                    )

                    chunk_records.append({
                        "method": method_name,
                        "contract_id": contract_id,
                        "context_group_id":
                            context_group_id,
                        "chunk_id":
                            f"{contract_id}__chunk_{chunk_number:04d}",
                        "chunk_number": chunk_number,
                        "char_start": char_start,
                        "char_end": char_end,
                        "num_tokens":
                            (end_token - start_token)
                            + num_special_tokens
                    })

                    chunk_number += 1

                    # Stop once the entire paragraph has been used.
                    if end_token == paragraph_token_count:
                        break

                continue


            # CASE 2:
            # Paragraph fits inside the current chunk.
            if (
                current_token_count
                + paragraph_token_count
                <= max_content_tokens
            ):

                # If this is the first paragraph in the chunk, record its starting character.
                if current_start is None:
                    current_start = paragraph_start

                current_end = paragraph_end

                current_token_count += (
                    paragraph_token_count
                )


            # CASE 3:
            # If adding this paragraph would exceed 512 tokens, save the current chunk and begin a new chunk with this paragraph.

            else:

                chunk_records.append({
                    "method": method_name,
                    "contract_id": contract_id,
                    "context_group_id": context_group_id,
                    "chunk_id":
                        f"{contract_id}__chunk_{chunk_number:04d}",
                    "chunk_number": chunk_number,
                    "char_start": current_start,
                    "char_end": current_end,
                    "num_tokens":
                        current_token_count
                        + num_special_tokens
                })

                chunk_number += 1

                # Start a new chunk with this paragraph.
                current_start = paragraph_start
                current_end = paragraph_end
                current_token_count = (
                    paragraph_token_count
                )

        # Save the last unfinished chunk in the contract.

        if current_start is not None:

            chunk_records.append({
                "method": method_name,
                "contract_id": contract_id,
                "context_group_id": context_group_id,
                "chunk_id":
                    f"{contract_id}__chunk_{chunk_number:04d}",
                "chunk_number": chunk_number,
                "char_start": current_start,
                "char_end": current_end,
                "num_tokens":
                    current_token_count
                    + num_special_tokens
            })

    return pd.DataFrame(chunk_records)