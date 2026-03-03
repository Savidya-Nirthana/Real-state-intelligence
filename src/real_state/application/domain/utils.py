import re
from typing import List

def format_docs(docs: list)-> str:
    """
    Format list of Documets into a single context string.
    Args:
        docs: List of Langchain Document objects

    Returns:
        Formatted context string with source URLs
    """
    formatted=[]
    for i, doc in enumerate(docs,1):
        url = doc.get('url', 'N/A')
        project_id = doc.get('project_id', 'N/A')
        title = doc.get('title', 'N/A')
        content = doc.get('text', 'N/A')[:500]
        formatted.append(
            f"[Source {i}: {url}]\n"
            f"Title: {title}\n"
            f"Project ID: {project_id}\n"
            f"Content: {content}\n"
        )
    
    return "\n---\n".join(formatted)
    
def calculate_confidence(docs: list, query: str) -> float:
    """
    calculate the confidence score for retrieved documents.
    
    Args:
        docs: List of retrived documents
        query: user query string

    returns: 
        confidence score 0.0 to 1.0
    """

    if not docs:
        return 0.0

    query_words = set(query.lower().split())

    overlaps = []
    for doc in docs:
        text = doc.get('text', '') if isinstance(doc, dict) else getattr(doc, 'page_content', '')
        doc_words = set(text.lower().split())
        overlap = len(query_words & doc_words) / len(query_words) if query_words else 0
        overlaps.append(overlap)
    
    keyword_score = sum(overlaps) / len(overlaps)
    
    avg_length = sum(
        len(doc.get('text', '') if isinstance(doc, dict) else getattr(doc, 'page_content', ''))
        for doc in docs
    ) / len(docs)
    length_score = min(avg_length / 500, 1.0)

    strategies = set([
        (doc.get('strategy', 'unknown') if isinstance(doc, dict) else doc.metadata.get('strategy', 'unknown'))
        for doc in docs
    ])
    diversity_score = len(strategies) / 5.0

    confidence = (keyword_score * 0.5 + length_score * 0.3 + diversity_score * 0.2)
    return confidence


def extract_citations(text: str) -> List[str]:
    """
    Extract citation numbers from the text.
    
    Args:
        text: Text containing citations
    
    Returns:
        List of citation numbers
    """
    citations = re.findall(r'\[([^\]]+)\]', text)

    return [c for c in citations if 'http' in c or '.com' in c]

def truncate_text(text: str, max_length: int = 400) -> str:
    """
    Truncate text to maximum length for quotes/previews.

    args:
        text: Text to maximum length for quotes/previews
        max_length: Maximum character length

    Returns:
        Truncated text with ellipsis if needed
    """

    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."  
