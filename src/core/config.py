"""Configuração centralizada do projeto AlupData.

Carrega variáveis de ambiente e secrets do GCP Secret Manager.
"""

import os


PROJECT_ID = os.getenv("GCP_PROJECT_ID", "alupdata-dev")
DATASET_BRONZE = os.getenv("BQ_DATASET_BRONZE", "bronze")
DATASET_SILVER = os.getenv("BQ_DATASET_SILVER", "silver")
DATASET_GOLD = os.getenv("BQ_DATASET_GOLD", "gold")
BUCKET_RAW = os.getenv("GCS_BUCKET_RAW", f"{PROJECT_ID}-raw")
