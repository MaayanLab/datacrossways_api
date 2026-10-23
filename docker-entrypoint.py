#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time

import psycopg2


def secret_value(name):
    file_name = os.environ.get(f"{name}_FILE")
    if file_name:
        with open(file_name, encoding="utf-8") as secret_file:
            return secret_file.read().strip()
    return os.environ.get(name)


def required(name):
    value = secret_value(name)
    if not value:
        raise SystemExit(f"Required environment variable {name} is empty")
    return value


def as_bool(name, default="false"):
    return os.environ.get(name, default).lower() in {"1", "true", "yes", "on"}


config = {
    "aws": {
        "aws_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "aws_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "bucket": os.environ.get("S3_BUCKET", ""),
        "region": os.environ.get("AWS_REGION", "us-east-1"),
    },
    "database": {
        "server": os.environ.get("DB_HOST", "postgres"),
        "port": os.environ.get("DB_PORT", "5432"),
        "name": os.environ.get("DB_NAME", "datacrossways"),
        "user": os.environ.get("DB_USER", "datacrossways"),
        "pass": required("DB_PASSWORD"),
    },
    "api": {"url": "http://api:5000/"},
    "frontend": {"url": "http://frontend/"},
    "redirect": {"url": os.environ.get("PUBLIC_BASE_URL", "http://localhost").rstrip("/")},
    "development": as_bool("DEVELOPMENT"),
}

if os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"):
    config["oauth"] = {
        "google": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": os.environ.get("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.environ.get("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        }
    }

os.makedirs("/app/secrets", exist_ok=True)
with open("/app/secrets/config.json", "w", encoding="utf-8") as config_file:
    json.dump(config, config_file, indent=2)
os.chmod("/app/secrets/config.json", 0o600)

os.environ["FLASK_SECRET_KEY"] = required("FLASK_SECRET_KEY")

for attempt in range(30):
    try:
        connection = psycopg2.connect(
            host=config["database"]["server"],
            port=config["database"]["port"],
            dbname=config["database"]["name"],
            user=config["database"]["user"],
            password=config["database"]["pass"],
        )
        connection.close()
        break
    except psycopg2.OperationalError:
        if attempt == 29:
            raise
        time.sleep(2)

subprocess.run([sys.executable, "/app/init_db.py"], check=True)
os.execvp(sys.argv[1], sys.argv[1:])
