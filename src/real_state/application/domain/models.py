from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


@dataclass
class Document:
    url: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.url:
            raise ValueError("Document URL cannot be empty")
        if not self.content:
            raise ValueError("Document content cannot be empty")
        
    
@dataclass 
class Chunk:
    text: str
    strategy: str
    chunk_index: int
    url: str
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.strategy not in ["semantic" , "fixed", "sliding"]:
            raise ValueError(f"Invalid chunking strategy: {self.strategy}")


