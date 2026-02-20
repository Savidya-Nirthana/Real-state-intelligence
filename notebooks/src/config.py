from pathlib import Path
from typing import Any, Dict, Optional
import os
import yaml


# =======================
# Project Path
# =======================

# get project root path
_PROJECT_ROOT = Path(__file__).parent.parent.parent
# get config directory
_CONFIG_DIR = _PROJECT_ROOT / "config"


# =========================
# yaml configurations
# =========================


def _load_yaml(filename: str) -> Dict[str, Any]:
    """ Load yaml config file """
    filepath = _CONFIG_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath , "r") as f:
        return yaml.safe_load(f) or {}

def _get_nested(d: Dict, *keys, default=None):
    """ Get nested value from dict """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d if d is not None else default



_CONFIG = _load_yaml("config.yaml")
_MODEL = _load_yaml("models.yaml")



PROVIDER = _get_nested(_CONFIG, "provider", "default" ,default="openrouter")
MODEL_TIER = _get_nested(_CONFIG, "provider", "tier", default="general")
OPENROUTER_BASE_URL = _get_nested(_CONFIG, "provider", "openrouter", "base_utl", default="https://openrouter.ai/api/v1")


def get_chat_model(provider: Optional[str] = None, tier: Optional[str] = None) -> str:
    """ Get chat model name """
    provider = provider or PROVIDER
    tier = tier or MODEL_TIER

    return _get_nested(_MODEL, provider, "chat", tier, default="google/gemini-2.5-flash")


def get_embedding_model(provider: Optional[str] = None, tier: str = "default") -> str:
    """ Get embedding model name """
    provider = provider or PROVIDER

    return _get_nested(_MODEL, provider, "embedding", tier, default="google/gemini-embedding-001")


CHAT_MODEL = get_chat_model()
EMBEDDING_MODEL = get_embedding_model()



