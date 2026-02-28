from typing import List, Dict, Any, Optional, Tuple
import tiktoken
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)

from real_state.config import (
    FIXED_CHUNK_SIZE,
    FIXED_CHUNK_OVERLAP,
    SEMANTIC_MIN_CHUNK_SIZE,
    SEMANTIC_MAX_CHUNK_SIZE,
    PARENT_CHUNK_SIZE,
    CHILD_CHUNK_SIZE,
    SLIDING_STRIDE_SIZE,
    SLIDING_WINDOW_SIZE,
    CHILD_OVERLAP, 
    LATE_CHUNK_BASE_SIZE,
    LATE_CHUNK_CONTEXT_WINDOW,
    LATE_CHUNK_SPLIT_SIZE
    
)
from real_state.application.domain.models import Chunk, Document


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    count tokens in text using tiktokens
    """
    try: 
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def sementic_chunk(document: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    chunk_idx = 0

    headers_to_split = [
        ('#' , 'h1'),
        ('##', 'h2'),
        ('###', 'h3'),
    ]

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split,
        strip_headers=False
    )

    for doc in document: 
        content = doc['content']
        url = doc['url']
        title = doc['title']

        try:
            sections = splitter.split_text(content)

            if not sections:
                sections = [type('obj', (object,), {'page_content': content, 'metadata': {}})()]
            
            for section in sections:
                text = section.page_content.strip()

                if not text or len(text) < SEMENTIC_MIN_CHUNK_SIZE:
                    continue

                if count_tokens(text) > SEMANTIC_MAX_CHUNK_SIZE:
                    char_size = SEMANTIC_MAX_CHUNK_SIZE * 4
                    sub_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=char_size,
                        chunk_overlap=100,
                        length_function=len
                    )

                    sub_chunks = sub_splitter.split_text(text)

                    if sub_text.strip():
                        chunks.append({
                            "url": url,
                            "title" : title,
                            "text" : sub_text.strip(),
                            "strategy" : "semantic",
                            "chunk_index" : chunk_idx,
                            "heading" : section.metadata.get("h1", "") or section.metadata.get("h2", "")

                        })

                        chunk_idx += 1

                else:
                    chunks.append({
                        "url" : url, 
                        "title": title,
                        "text" : text,
                        "strategy" : "semantic",
                        "chunk_index" : chunk_idx,
                        "heading" : section.metadata.get("h1", "") or section.metadata.get("h2", "")
                    })

                    chunk_idx += 1
        except Exception as e:
            if content.strip():
                chunks.append({
                    "url" : url,
                    "title" : title,
                    "text" : content.strip(),
                    "strategy" : "semantic",
                    "chunk_index" : chunk_idx,
                    "heading" : ""
                })

                chunk_idx += 1
    
    return chunks

def fixed_chunk(document: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    chunk_idx = 0

    chunk_size_chars = FIXED_CHUNK_SIZE * 4
    overlap_chars = FIXED_CHUNK_OVERLAP * 4

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_chars,
        chunk_overlap=overlap_chars,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    for doc in document:
        content = doc['content']
        url = doc['url']
        title = doc['title']


        doc_chunks = splitter.split_text(content)

        for text in doc_chunks:
            if text.strip():
                token_count = count_tokens(text)
                chunks.append({
                    "url" : url,
                    "title" : title,
                    "text": text.strip(),
                    "strategy" : "fixed",
                    "chunk_index" : chunk_idx,
                    "token_count" : token_count,
                    "overlap_tokens" : FIXED_CHUNK_OVERLAP
                })

                chunk_idx += 1
    
    return chunks


def sliding_chunks(document: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    chunk_idx = 0

    window_size_chars = SLIDING_WINDOW_SIZE * 4
    stride_chars = SLIDING_STRIDE_SIZE * 4

    for doc in document:
        content = doc['content']
        url = doc['url']
        title = doc['title']

        pos = 0
        window_idx = 0
        content_len = len(content)

        while pos < content_len:
            end = min(pos + window_size_chars, content_len)
            window_text = content[pos:end]


            if window_text.strip():
                chunks.append({
                    "url" : url,
                    "title" : title,
                    "text" : window_text.strip(),
                    "strategy" : "sliding",
                    "chunk_index": chunk_idx,
                    "window_index" : window_idx,
                    "overlap_tokens" : SLIDING_STRIDE_SIZE if window_idx > 0 else 0
                })
                chunk_idx += 1
                window_idx += 1

            pos += stride_chars
            if pos >= content_len:
                break

    return chunks


def parent_child_chunk(document: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    parent_chunks = []
    child_chunks = []
    parent_idx = 0
    child_idx = 0

    parent_size_chars = PARENT_CHUNK_SIZE * 4
    child_size_chars = CHILD_CHUNK_SIZE * 4 
    child_overlap_chars = CHILD_OVERLAP * 4

    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size = parent_size_chars,
        chunk_overlap = 200,
        length_function = len
    )

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size = child_size_chars,
        chunk_overlap = child_overlap_chars,
        length_function = len
    )

    for doc in document:
        content = doc['content']
        url = doc['url']
        title = doc['title']

        parent_texts = parent_splitter.split_text(content)

        for parent_text in parent_texts:
            if not parent_text.strip():
                continue

            parent_id = f"{url}::parent::{parent_idx}"

            parent_chunks.append({
                "parent_id" : parent_id,
                "url" : url,
                "title" : title,
                "text" : parent_text.strip(),
                "strategy" : "parent",
                "chunk_index": parent_idx,
                "token_count": count_tokens(parent_text)
            })

            child_texts = child_splitter.split_text(parent_text)

            for child_text in child_texts:
                if child_text.strip():
                    child_chunks.append({
                        "child_id" : f"{parent_id}::child::{child_idx}",
                        "parent_id" : parent_id,
                        "url" : url,
                        "title" : title,
                        "text" : child_text.strip(),
                        "strategy": "child",
                        "chunk_index" : child_idx,
                        "token_count" : count_tokens(child_text)
                    })
                    child_idx += 1
            parent_idx += 1

    return child_chunks, parent_chunks



def late_chunk_index(document: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    chunk_idx = 0

    base_size_chars = LATE_CHUNK_SIZE * 4

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = base_size_chars,
        chunk_overlap = 200,
        length_function = len
    )

    for doc in document:
        content = doc['content']
        url = doc['url']
        title = doc['title']

        passages = splitter.split_text(content)

        for passage in passages:
            if passage.strip():
                chunks.append({
                    "url" : url,
                    "title" : title,
                    "text" : passage.strip(),
                    "strategy" : "late_chunk_base",
                    "chunk_index" : chunk_idx,
                    "token_count" : count_tokens(passage),
                    "splittable" : True
                })

                chunk_idx += 1
    return chunks



def late_chunk_split(passage: str, query: str) -> List[Dict[str, Any]]:
    query_terms = query.lower().split()
    passage_lower = passage.lower()

    match_positions = []
    for term in query_terms:
        pos = 0
        while True:
            pos = passage_lower.find(term, pos)
            if pos == -1:
                break
            match_positions.append(pos)
            pos += len(term)

    if not match_positions:
        return [{"text" : passage, "score" : 0.0}]

    chunks = []
    context_chars = LATE_CHUNK_CONTEXT_WINDOW * 4
    split_size_chars = LATE_CHUNK_SPLIT_SIZE * 4

    for match_pos in match_positions:
        start = max(0, match_pos - context_chars)
        end = min(len(passage), match_pos + split_size_chars)

        chunk_text = passage[start:end].strip()

        score = 1.0 if match_pos in match_positions else 0.5

        chunks.append({
            "text" : chunk_text,
            "match_position" : match_pos,
            "score" : score,

        })

    unique_chunks = []
    seen_texts = set()

    for chunk in sorted(chunks, key=lambda x: x['score'], reverse=True):
        if chunk['text'] not in seen_texts:
            unique_chunks.append(chunk)
            seen_texts.add(chunk['text'])

    return unique_chunks[:5]


class ChunkingService:

    def __init__(self):
        self.strategies = {
            "semantic": semantic_chunk,
            "fixed": fixed_chunk,
            "sliding": sliding_chunk,
            "parent_child": parent_child_chunk,
            "late_chunk": late_chunk_index
        }
        
    def chunk(
        self,
        document: List[Dict[str, Any]],
        strategy: str = "semantic"
    )-> Any:
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        return self.strategies[strategy](document)

    def available_strategies(self) -> List[str]:
        return list(self.strategies.keys())



__all__ = [
    "semantic_chunk",
    "fixed_chunk",
    "sliding_chunk",
    "parent_child_chunk",
    "late_chunk_index",
    "late_chunk_split",
    "ChunkingService",
    "count_tokens"
]