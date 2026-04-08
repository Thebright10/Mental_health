import pandas as pd

# read TSV files (NO header)
train = pd.read_csv("../dataset/train.tsv", sep="\t", header=None)
test = pd.read_csv("../dataset/test.tsv", sep="\t", header=None)
dev = pd.read_csv("../dataset/dev.tsv", sep="\t", header=None)

# combine datasets
data = pd.concat([train, test, dev])

# set correct column names
data.columns = ["text", "labels", "id"]

print("Dataset loaded:", data.shape)

# keep only text + emotion label
data = data[["text", "labels"]]

# if multiple emotions exist keep first one
data["labels"] = data["labels"].astype(str).str.split(",").str[0]

# save processed dataset
data.to_csv("../dataset/goemotions_combined.csv", index=False)

print("Dataset processed successfully")