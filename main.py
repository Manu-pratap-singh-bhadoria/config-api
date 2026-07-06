import os
import yaml
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

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).lower() in ["true", "1", "yes", "on"]


def coerce(key, value):
    if key in ["port", "workers"]:
        return int(value)
    elif key == "debug":
        return to_bool(value)
    return str(value)


def load_yaml():
    if not os.path.exists("config.development.yaml"):
        return {}

    with open("config.development.yaml", "r") as f:
        data = yaml.safe_load(f)

    return data or {}


def load_env():
    result = {}

    for key, value in os.environ.items():
        if key.startswith("APP_"):
            new_key = key[4:].lower()
            result[new_key] = value

    # Alias: NUM_WORKERS -> workers
    if "num_workers" in result:
        result["workers"] = result.pop("num_workers")

    return result


@app.get("/effective-config")
def effective_config(
    set_port: int = Query(None, alias="set-port"),
    set_workers: int = Query(None, alias="set-workers"),
    set_debug: str = Query(None, alias="set-debug"),
    set_log_level: str = Query(None, alias="set-log_level"),
    set_api_key: str = Query(None, alias="set-api_key"),
):
    config = DEFAULTS.copy()

    # YAML
    yaml_config = load_yaml()
    for key, value in yaml_config.items():
        config[key] = coerce(key, value)

    # Environment
    env_config = load_env()
    for key, value in env_config.items():
        config[key] = coerce(key, value)

    # Query overrides
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
