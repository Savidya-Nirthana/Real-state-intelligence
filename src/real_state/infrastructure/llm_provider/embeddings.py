from typing import Optional, Any
import os
from langchain_openai import OpenAIEmbeddings

from real_state.config import (
    PROVIDER,
    EMBEDDING_MODEL,
    EMBEDDING_SHOW_PROGRESS,
    EMBEDDING_BATCH_SIZE,
    get_api_key,
    get_embedding_model,
    OPENROUTER_BASE_URL
)

def get_default_embeddings(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    tier: str = "default",
    batch_size: Optional[int] = None,
    show_progress: Optional[bool] = None,
    **kwargs: Any
) -> OpenAIEmbeddings:
    use_provider = provider or PROVIDER

    if model: 
        use_model = model
    else:
        use_model = get_embedding_model(provider=use_provider, tier=tier)

    if "/" in use_model:
        use_model = use_model.split("/")[-1]
        
    api_key = get_api_key(provider=use_provider)

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    use_batch_size = batch_size if batch_size is not None else EMBEDDING_BATCH_SIZE
    use_show_progress = show_progress if show_progress is not None else EMBEDDING_SHOW_PROGRESS

    if use_provider == "openrouter":
        return OpenAIEmbeddings(
            model=use_model,
            openai_api_key=api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            show_progress=use_show_progress,
            **kwargs
        )
    else:
        return OpenAIEmbeddings(
            model=use_model,
            openai_api_key=api_key,
            show_progress_bar=use_show_progress,
            **kwargs
        )


def get_small_embeddings(**kwargs: Any) -> OpenAIEmbeddings:
    return get_default_embeddings(tier="small", **kwargs)