from pathlib import Path
from typing import Any, Dict, Optional, List
import os
import yaml
from dotenv import load_dotenv


load_dotenv()

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



LLM_TEMPERATURE = _get_nested(_CONFIG, "llm", "temperature", default = 0.0)
LLM_MAX_TOKENS = _get_nested(_CONFIG, "llm", "max_tokens", default = 2000)
LLM_STREAMING = _get_nested(_CONFIG, "llm", "streaming", default = False)


EMBEDDING_BATCH_SIZE = _get_nested(_CONFIG, "embedding", "batch_size", default = 100)
EMBEDDING_SHOW_PROGRESS = _get_nested(_CONFIG, "embedding", "show_progress", default = False)

BASE_URL = _get_nested(_CONFIG, "base_url", default="https://www.primelands.lk")


DATA_DIR  = _PROJECT_ROOT / _get_nested(_CONFIG, "paths", "data_dir", default="data")
VECTOR_DIR  = _PROJECT_ROOT / _get_nested(_CONFIG, "paths", "vector_dir", default="data/vector_store")
MARKDOWN_DIR  = _PROJECT_ROOT / _get_nested(_CONFIG, "paths", "markdown_dir", default="data/primeland_markdown")
CACHE_DIR  = _PROJECT_ROOT / _get_nested(_CONFIG, "paths", "cache_dir", default="data/cag_cache")
CRAWL_OUT_DIR = DATA_DIR

FIXED_CHUNK_SIZE = _get_nested(_CONFIG, "chunking", "fixed" , "chunk_size", default=1000)
FIXED_CHUNK_OVERLAP = _get_nested(_CONFIG, "chunking", "fixed" , "chunk_overlap", default=100)

SEMANTIC_MAX_CHUNK_SIZE = _get_nested(_CONFIG, "chunking", "semantic", "max_chunk_size", default=1000)
SEMANTIC_MIN_CHUNK_SIZE = _get_nested(_CONFIG, "chunking", "semantic", "min_chunk_size", default=200)


SLIDING_WINDOW_SIZE = _get_nested(_CONFIG, "chunking", "sliding", "window_size", default=512)
SLIDING_STRIDE_SIZE = _get_nested(_CONFIG, "chunking", "sliding", "stride_size", default=256)

PARENT_CHUNK_SIZE = _get_nested(_CONFIG, "chunking", "parent_child", "parent_size", default=1200)
CHILD_CHUNK_SIZE = _get_nested(_CONFIG, "chunking", "parent_child", "child_size", default=250)
CHILD_OVERLAP = _get_nested(_CONFIG, "chunking", "parent_child", "child_overlap", default=50)

LATE_CHUNK_BASE_SIZE = _get_nested(_CONFIG, "chunking", "late", "base_size", default=1000)
LATE_CHUNK_SPLIT_SIZE = _get_nested(_CONFIG, "chunking", "late", "split_size", default=300)
LATE_CHUNK_CONTEXT_WINDOW = _get_nested(_CONFIG, "chunking", "late", "context_window", default=150)

TOP_K_RESULTS = _get_nested(_CONFIG, "retrieval", "top_k", default=4)
SIMILARITY_THRESHOLD = _get_nested(_CONFIG, "retrieval", "similarity_threshold", default=0.7)

CAG_CACHE_TTL = _get_nested(_CONFIG, "cag", "cache_ttl", default=86400)
CAG_CACHE_MAX_SIZE = _get_nested(_CONFIG, "cag", "max_cache_size", default=1000)
CAG_SIMILARITY_THRESHOLD = _get_nested(_CONFIG, "cag", "similarity_threshold", default=0.90)
CAG_HISTORY_TTL_HOURS = _get_nested(_CONFIG, "cag", "history_ttl_hours", default=24)



def load_faqs() -> List:
    faqs_config = _load_yaml("faqs.yaml")
    all_faqs = []

    for category, questions in faqs_config.items():
        if isinstance(questions, list):
            all_faqs.extend(questions)
    return all_faqs


KNOWN_FAQS = load_faqs()

CRAG_CONFIDENCE_THRESHOLD = _get_nested(_CONFIG, "crag", "confidence_threshold", default=0.6)
CRAG_EXPANDED_K = _get_nested(_CONFIG, "crag", "expanded_k", default=8)

CRAWL_MAX_DEPTH = _get_nested(_CONFIG, "crawling", "max_depth", default=3)
CRAWL_DELAY_SECONDS = _get_nested(_CONFIG, "crawling", "delay_seconds", default=2.0)
CRAWL_MAX_PAGES = _get_nested(_CONFIG, "crawling", "max_pages", default=100)



def get_api_key(provider: str = None) -> str:
    """ Get API key for provider """
    provider = provider or PROVIDER
    key_map = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY"
    }

    env_var = key_map.get(provider)
    return os.getenv(env_var)


def validate() -> None:
    api_key = get_api_key()
    if not api_key:
        key_name = "OPENROUTER_API_KEY" if PROVIDER == "openrouter" else f"{PROVIDER.upper()}_API_KEY"
        raise ValueError(f"API key not found for provider: {PROVIDER}")


    required_dir = [DATA_DIR, VECTOR_DIR, MARKDOWN_DIR, CACHE_DIR]
    for dir_path in required_dir:
        try: 
            dir_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}")


def dump() -> None:
    """Print all active non-secret config values"""
    print("\n" + "=" * 60)
    print("CONFIGURATION (NON-SECRETS ONLY)")
    print("=" * 60)
    
    print("\n🌐 Provider:")
    print(f"   Provider: {PROVIDER}")
    print(f"   Model Tier: {MODEL_TIER}")
    print(f"   Chat Model: {CHAT_MODEL}")
    print(f"   Embedding Model: {EMBEDDING_MODEL}")
    
    print("\n📁 Directories:")
    print(f"   Data Root: {DATA_DIR}")
    print(f"   Vector Store: {VECTOR_DIR}")
    print(f"   Markdown: {MARKDOWN_DIR}")
    print(f"   Cache: {CACHE_DIR}")
    
    print("\n🔧 Chunking:")
    print(f"   Fixed Size: {FIXED_CHUNK_SIZE} tokens")
    print(f"   Fixed Overlap: {FIXED_CHUNK_OVERLAP} tokens")
    print(f"   Sliding Window: {SLIDING_WINDOW_SIZE} tokens")
    print(f"   Sliding Stride: {SLIDING_STRIDE_SIZE} tokens")
    print(f"   Parent-Child: {CHILD_CHUNK_SIZE} → {PARENT_CHUNK_SIZE} tokens")
    print(f"   Late Chunk: {LATE_CHUNK_BASE_SIZE} → {LATE_CHUNK_SPLIT_SIZE} tokens")
    
    print("\n🔍 Retrieval:")
    print(f"   Top-K Results: {TOP_K_RESULTS}")
    print(f"   Similarity Threshold: {SIMILARITY_THRESHOLD}")
    
    print("\n💾 CAG:")
    print(f"   Cache TTL: {CAG_CACHE_TTL}s")
    print(f"   Max Cache Size: {CAG_CACHE_MAX_SIZE}")
    
    print("\n🎯 CRAG:")
    print(f"   Confidence Threshold: {CRAG_CONFIDENCE_THRESHOLD}")
    print(f"   Expanded K: {CRAG_EXPANDED_K}")
    
    print("\n" + "=" * 60 + "\n")
    


def get_all_models() -> Dict[str, Any]:
    """Return all available models"""
    return _MODEL


def get_config() -> Dict[str, Any]:
    """Return all available config"""
    return _CONFIG



