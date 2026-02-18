import os

DB_PATH = os.environ.get("DB_PATH", "./data/chat.db")

QA_MODELS = [
    {"id": "tinybert", "name": "TinyBERT", "model": "Intel/dynamic_tinybert"},
    {"id": "deberta-v3-base", "name": "DeBERTa v3 Base", "model": "deepset/deberta-v3-base-squad2"},
    {"id": "electra-base", "name": "ELECTRA Base", "model": "deepset/electra-base-squad2"},
    {"id": "roberta-large", "name": "RoBERTa Large", "model": "deepset/roberta-large-squad2"},
]
QA_DEFAULT_MODEL = "tinybert"

NER_MODEL = "dslim/bert-base-NER"
