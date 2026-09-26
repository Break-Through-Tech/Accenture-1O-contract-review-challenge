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