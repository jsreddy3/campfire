import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

def load_config() -> Dict[str, Any]:
    # Config is in parent directory (app/)
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def get_openai_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return api_key

CONFIG = load_config()
OPENAI_API_KEY = get_openai_api_key()