"""
LLM provider with openrouter support for multi provider access.
Set OPENROUTER_API_KEY in .env file

"""


from typing import Optional, Any, List
import os 
from langchain_openai import ChatOpenAI
from real_state.config import (
    PROVIDER,
    CHAT_MODEL,
    OPENROUTER_BASE_URL,
    LLM_STREAMING,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    get_api_key, 
    get_chat_model
)

def get_chat_llm(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    tier: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    streaming: Optional[bool] = None
)-> ChatOpenAI:
    """
    Factory function to get chat LLM instance
    """
    
    use_provider = provider or PROVIDER
    
    if model:
        use_model = model
    elif tier:
        use_model = get_chat_model(provider=use_provider, tier=tier)
    else:
        use_model = CHAT_MODEL

    api_key = get_api_key(use_provider)

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")


    use_base_url = OPENROUTER_BASE_URL if use_provider == "openrouter" else None
    use_temperature = temperature or LLM_TEMPERATURE
    use_max_tokens = max_tokens or LLM_MAX_TOKENS
    use_streaming = streaming or LLM_STREAMING

    if use_provider == "openrouter":
        return ChatOpenAI(
            model=use_model,
            openai_api_key=api_key,
            openai_api_base=use_base_url,
            temperature=use_temperature,
            max_tokens=use_max_tokens,
            streaming=use_streaming
        )
    else:
        return ChatOpenAI(
            model=use_model,
            openai_api_key=api_key,
            temperature=use_temperature,
            max_tokens=use_max_tokens,
            streaming=use_streaming
        )

    
def get_reasoning_llm(**kwargs: Any) -> ChatOpenAI:
    """ Get a reasoning LLM instance """
    return get_chat_llm(tier='reason', **kwargs)

def get_strong_llm(**kwargs: Any) -> ChatOpenAI:
    """ Get high-capability LLM instance """
    return get_chat_llm(tier='strong', **kwargs)


def list_available_models() -> List[str]:
    """ List all available models """
    return get_chat_model()