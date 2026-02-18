import os

DB_PATH = os.environ.get("DB_PATH", "./data/chat.db")

QA_MODELS = [
    {"id": "tinybert", "name": "TinyBERT", "model": "Intel/dynamic_tinybert"},
    {"id": "distilbert", "name": "DistilBERT", "model": "distilbert/distilbert-base-cased-distilled-squad"},
    {"id": "roberta-base", "name": "RoBERTa Base", "model": "deepset/roberta-base-squad2"},
    {"id": "roberta-large", "name": "RoBERTa Large", "model": "deepset/roberta-large-squad2"},
    {"id": "bert-large", "name": "BERT Large", "model": "google-bert/bert-large-uncased-whole-word-masking-finetuned-squad"},
]
QA_DEFAULT_MODEL = "distilbert"
