import requests
import pandas as pd
from io import StringIO, BytesIO

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
    else:
        raise ValueError(f"File type not supported: {path_from_root}")

def load_split_data(split_name: str, data_dir="split_data", split_dir="frozen-split_data"):
    """
    Loads all CUAD tables and filters them down to one split ("train" or "val"),
    based on the frozen split map (context-group-level split, contract-level in practice).
    :param split_name: the name of the split to load
    :param data_dir: the directory where the data is located
    :param split_dir: the directory where the data is located
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

    return {
        "contracts": split_contracts,
        "documents": split_documents,
        "categories": categories,          # not split-specific
        "annotation_sets": split_annotation_sets,
        "spans": split_spans,
    }
