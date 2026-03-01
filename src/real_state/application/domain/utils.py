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
    