from utils import load_file_from_github

categories = load_file_from_github("data/cuad/category_descriptions.csv", branch="setup-and-explore")

print(categories)