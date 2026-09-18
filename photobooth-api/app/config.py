import json
import os
from functools import lru_cache

import boto3

# Variables de entorno NO sensibles (nombres/identificadores, no credenciales)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DB_SECRET_NAME = os.environ.get("DB_SECRET_NAME", "photobooth/db-credentials")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")


@lru_cache(maxsize=1)
def get_db_credentials() -> dict:

    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=DB_SECRET_NAME)
    secret = json.loads(response["SecretString"])
    return secret


def get_database_url() -> str:
    creds = get_db_credentials()
    user = creds["username"]
    password = creds["password"]
    host = creds["host"]
    port = creds.get("port", 5432)
    dbname = creds.get("dbname", "photobooth")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
