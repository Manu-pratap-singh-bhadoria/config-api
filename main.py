import os
import yaml
import argparse
from fastapi import FastAPI, Query
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DEFAULTS ----------------

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


# ---------------- HELPERS ----------------

def to_bool(value):
    return str(value).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)


# ---------------- YAML ----------------

def load_yaml():
    if not os.path.exists("config.development.yaml"):
        return {}

    with open("config.development.yaml", "r") as f:
        data = yaml.safe_load(f)

    return data or {}


# ---------------- ENV ----------------

def load_env():
    result = {}

    for key, value in os.environ.items():

        if key.startswith("APP_"):
            result[key[4:].lower()] = value

    # APP_NUM_WORKERS -> workers
    if "num_workers" in result:
        result["workers"] = result.pop("num_workers")

    return result


# ---------------- CLI ----------------

parser = argparse.ArgumentParser(add_help=False)

parser.add_argument("--port")
parser.add_argument("--workers")
parser.add_argument("--debug")
parser.add_argument("--log_level")
parser.add_argument("--api_key")

args, _ = parser.parse_known_args()

CLI_CONFIG = {}

for key, value in vars(args).items():
    if value is not None:
        CLI_CONFIG[key] = value


# ---------------- API ----------------

@app.get("/effective-config")
def effective_config(
    set_port: int | None = Query(None, alias="set-port"),
    set_workers: int | None = Query(None, alias="set-workers"),
    set_debug: str | None = Query(None, alias="set-debug"),
    set_log_level: str | None = Query(None, alias="set-log_level"),
    set_api_key: str | None = Query(None, alias="set-api_key"),
):
    config = DEFAULTS.copy()

    # YAML
    for key, value in load_yaml().items():
        config[key] = coerce(key, value)

    # ENV
    for key, value in load_env().items():
        config[key] = coerce(key, value)

    # CLI
    for key, value in CLI_CONFIG.items():
        config[key] = coerce(key, value)

    # QUERY PARAMS
    if set_port is not None:
        config["port"] = set_port

    if set_workers is not None:
        config["workers"] = set_workers

    if set_debug is not None:
        config["debug"] = to_bool(set_debug)

    if set_log_level is not None:
        config["log_level"] = set_log_level

    if set_api_key is not None:
        config["api_key"] = set_api_key

    # Mask secret
    config["api_key"] = "*****"

    return config