import hashlib
import pickle
from dataclasses import dataclass

import requests
import pandas as pd
from io import StringIO, BytesIO

@dataclass
class CUAD:
    contracts: pd.DataFrame
    documents: pd.DataFrame
    categories: pd.DataFrame
    annotation_sets: pd.DataFrame
    spans: pd.DataFrame

def load_file_from_github(path_from_root: str, branch: str="main"):
    """
    Retrieves JSON file from the Accenture 1O repository
    :param path_from_root: the path to the file from the branch's root
    :param branch: the branch the file is located on, assumes "main" branch
    :return: the file as a json object or pandas dataframe according to the file type
    """
    path_from_root = path_from_root.strip()
    url = f"https://raw.githubusercontent.com/Break-Through-Tech/Accenture-1O-contract-review-challenge/{branch}/{path_from_root}"

    response = requests.get(url)
    response.raise_for_status()

    if path_from_root.endswith(".json"):
        return response.json()
    elif path_from_root.endswith(".csv"):
        return pd.read_csv(StringIO(response.text))
    elif path_from_root.endswith(".parquet"):
        return pd.read_parquet(BytesIO(response.content))
    elif path_from_root.endswith(".pkl"):
        with open("frozen_scorecards.pkl", "rb") as f:
            file_contents = pickle.load(f)
        return file_contents
    else:
        raise ValueError(f"File type not supported: {path_from_root}")

def normalize_cuad(data: dict, cuad=False) -> dict | CUAD:
    """
    Normalizes the given CUAD dataset from nested JSON objects into separate actionable DataFrames
    :param cuad:
    :param data: list of document objects from the CUAD dataset
    :return: a single dictionary that contains separate DataFrames for contracts, documents, categories, annotation sets, and spans. These DataFrames are connected via 'foreign keys' (aka their IDs)
    """

    # assign contract ids for each contract in the dataset
    for i, item in enumerate(data):
        item["contract_id"] = f"contract_{i + 1:04d}"

    # get each document and their respective data (title, context, qas)
    documents = pd.json_normalize(
        data,
        record_path="paragraphs",
        meta=["title", "contract_id"]
    )[["contract_id", "title", "context"]]

    # assign ids and hashes
    documents["document_id"] = [f"document_{i + 1:04d}" for i in range(len(documents))]
    documents["context_group_id"] = documents["context"].apply(
        lambda c: "context_" + hashlib.md5(c.encode("utf-8")).hexdigest()[:10]
    )

    # create the contracts "table" and remove duplicates
    contracts = (
        documents[["contract_id", "title"]]
        .drop_duplicates(subset="contract_id")
        .reset_index(drop=True)
    )

    # ensures all indexes are correct
    documents = documents[
        ["document_id", "contract_id", "context", "context_group_id"]
    ].reset_index(drop=True)

    # get all Q&A objects
    qas = pd.json_normalize(
        data,
        record_path=["paragraphs", "qas"],
        meta=["title", "contract_id"]
    )

    qas["category_name"] = qas["question"].str.extract(f'"([^"]+)')
    qas["category_id"] = (
        qas["category_name"]
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    qas["annotation_set_id"] = qas["contract_id"] + "__" + qas['category_id'].str.lower()

    # get categories. each question typically corresponds to a category
    categories = (
        qas[["category_id", "category_name", "question"]]
        .drop_duplicates(subset="category_id")
        .reset_index(drop=True)
    )

    # get the annotation set: one contract paired with one clause category/question
    annotation_sets = (
        qas.groupby(
            ["annotation_set_id", "contract_id", "category_id"]
        , as_index=False)["is_impossible"]
        .all()
    )

    # get each span: one individual answer inside the Q&A's answer list
    spans = qas[["answers", "id", "annotation_set_id"]].explode("answers")
    spans = spans[spans["answers"].notna()].copy() # drops impossible rows

    # expand the answer fields to be included in the top-level columns
    answer_fields = pd.json_normalize(spans["answers"])
    spans = pd.concat([spans.drop(columns="answers"), answer_fields], axis=1)

    spans = spans.rename(columns={"id": "source_qa_id", "text": "answer_text"})
    spans["answer_end"] = spans["answer_start"] + spans["answer_text"].str.len()

    # create the span id
    num_spans = spans.groupby("annotation_set_id").cumcount()
    spans["span_id"] = (
        spans["annotation_set_id"] + "__span_" + num_spans.astype(str).str.zfill(3)
    )
    spans = spans[[
        "span_id",
        "annotation_set_id",
        "source_qa_id",
        "answer_text",
        "answer_start",
        "answer_end",
    ]].reset_index(drop=True)

    return CUAD(
        contracts=contracts,
        documents=documents,
        categories=categories,
        annotation_sets=annotation_sets,
        spans=spans,
    ) if cuad else {
        "contracts": contracts,
        "documents": documents,
        "categories": categories,
        "annotation_sets": annotation_sets,
        "spans": spans,
    }


def load_split_data(split_name: str, data_dir="split_data", split_dir="frozen-split_data", cuad=False):
    """
    Loads all CUAD tables and filters them down to one split ("train" or "val"),
    based on the frozen split map (context-group-level split, contract-level in practice).
    :param split_name: the name of the split to load
    :param data_dir: the directory where the data is located
    :param split_dir: the directory where the data is located
    :param cuad: boolean flag indicating whether to load the data as a CUAD object or dict
    :return: a dict containing a pandas dataframe for all cuad-tables
    """
    contracts = pd.read_parquet(f"{data_dir}/contracts.parquet")
    documents = pd.read_parquet(f"{data_dir}/documents.parquet")
    categories = pd.read_parquet(f"{data_dir}/categories.parquet")
    annotation_sets = pd.read_parquet(f"{data_dir}/annotation_sets.parquet")
    spans = pd.read_parquet(f"{data_dir}/spans.parquet")
    split_map = pd.read_parquet(f"{split_dir}/frozen-split.parquet")

    documents = documents.merge(split_map, on="context_group_id", how="left")

    unmatched = documents["split"].isna().sum()
    if unmatched:
        print(f"WARNING: {unmatched} documents with no split label")

    split_documents = documents[documents["split"] == split_name].copy()
    split_contract_ids = set(split_documents["contract_id"])

    split_contracts = contracts[contracts["contract_id"].isin(split_contract_ids)].copy()
    split_annotation_sets = annotation_sets[annotation_sets["contract_id"].isin(split_contract_ids)].copy()
    split_spans = spans[spans["annotation_set_id"].isin(split_annotation_sets["annotation_set_id"])].copy()

    return CUAD(
        contracts=split_contracts,
        documents=split_documents,
        categories=categories,
        annotation_sets=split_annotation_sets,
        spans=split_spans,
    ) if cuad else {
        "contracts": split_contracts,
        "documents": split_documents,
        "categories": categories,          # not split-specific
        "annotation_sets": split_annotation_sets,
        "spans": split_spans,
    }
