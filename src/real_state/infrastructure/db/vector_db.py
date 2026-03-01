from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import VectorParams, Distance, PointStruct
from datetime import datetime
import uuid
import os
from real_state.infrastructure.llm_provider.embeddings import get_default_embeddings
from real_state.config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
    QDRANT_TIMEOUT,
    QDRANT_URL,
    EMBEDDING_DIM,
    CRAWL_OUT_DIR
)

from typing import Dict, Any, List, Optional

class QdrantStorage:
    def __init__(self, url: str = None, api: str = None, embedding = get_default_embeddings() ,collection: str = 'prime_lands', timeout=30 ,dim=3072):
        self.embedding_dim = dim or EMBEDDING_DIM
        self.collection = collection or QDRANT_COLLECTION_NAME
        self.url = url or QDRANT_URL
        self.api = api or QDRANT_API_KEY
        self.timeout = timeout or QDRANT_TIMEOUT
        self.embedding = embedding or get_default_embeddings()

        self._qdrant_client = QdrantClient(
            url = self.url,
            api_key=self.api,
            timeout=30
        )


        if not self._qdrant_client.collection_exists(self.collection):
            self._qdrant_client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
            )

    
    def delete_collection(self, collection_name:str = None):
        """ Drop the entire collection (destructive) """
        collection_name = collection_name or QDRANT_COLLECTION_NAME
        
        try:
            self._qdrant_client.delete_collection(collection_name=collection_name)
            print(f"{collection_name} droped successfully")
        except Exception as e:
            print(e)
        
    def collection_info(self, collection_name: str = QDRANT_COLLECTION_NAME) -> Dict[str, Any]:
        """return collection stats (point count, vector size, etc.)"""
        info = self._qdrant_client.get_collection(collection_name=collection_name)
        return {
            "name" : collection_name,
            "points_count" : info.points_count,
            "index_vectors_count": info.indexed_vectors_count,
            "vector_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance.name,
            "status" : info.status.name 
        }

    def upsert_chunks(self, 
        chunks: List[Dict[str, Any]],
        collection_name: str = None,
        batch_size: int = 100
    ) -> int:
        """
        Upsert points into the collection

        each chunk dict is expected to contain at least:
             - text (str) : The chunk content.
             - url (str) : Souce url
             - title (str) : Source document title
             - project_id (str) : Source document project id
             - strategy (str) : Chunking strategy
             - chunk_index (int) : position in the original document


        payload : {
            url : str,
            title : str,
            project_id : str,
            strategy : str,
            chunk_index : int,
        }


        """
        collection_name = collection_name or QDRANT_COLLECTION_NAME
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]


            batch_embeddings = self.embedding.embed_documents([chunk["text"] for chunk in batch_chunks])


            if len(batch_embeddings) != len(batch_chunks):
                raise ValueError("Number of embeddings must match number of chunks")

            points = []
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                point_id = str(uuid.uuid4())
                payload = {
                    "text": chunk["text"],
                    "url": chunk["url"],
                    "title": chunk["title"],
                    "project_id": chunk["project_id"],
                    "strategy": chunk["strategy"],
                    "chunk_index": chunk["chunk_index"],
                }
                points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

            self._qdrant_client.upsert(
                collection_name=collection_name,
                points=points,
            )

        return len(chunks)

    def _extract_parent_chunks(self, child_chunk:Dict[str, Any]) -> List[Dict[str,Any]]:
        """
        Extract parent chunk from child chunk
        """
        parent_id = child_chunk.get("parent_id")
        if not parent_id:
            return None
        
        parent_path = CRAWL_OUT_DIR / "parent_chunk.jsonl"
        parent_chunks = []
        with open(parent_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    parent_chunks.append(json.loads(line))

        parent_chunk = [chunk for chunk in parent_chunks if chunk.get("parent_id") == parent_id]
        return parent_chunk

    def _ensure_payload_index(self, collection_name: str = None, field: str = "strategy"):
        """
        Ensure payload index exists for strategy field
        """
        collection_name = collection_name or QDRANT_COLLECTION_NAME
        try:
            self._qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass
        
        


    def search_chunks(self, 
        query: str = None,
        top_k: int = 4,
        score_threshold: float = 0.0,
        collection_name: str = None,
        strategy_filter: Optional[str] = None
    ):
        collection_name = collection_name or QDRANT_COLLECTION_NAME
        query_filter = None

        if strategy_filter:
            strategy_filter = strategy_filter.strip()
            
            self._ensure_payload_index(collection_name, "strategy")

            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="strategy",
                        match=models.MatchValue(value=strategy_filter)
                    )
                ]
            )
  
        query_vector = self.embedding.embed_query(query)
        
        search_result = self._qdrant_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold
        )

        results = []
        for hit in search_result.points:
            if hit.payload.get("strategy") == "child":
                parent_chunk = self._extract_parent_chunks(hit.payload)
                if parent_chunk:
                    hit.payload["text"] = parent_chunk[0]["text"]
                    hit.payload["strategy"] = parent_chunk[0]["strategy"]
                    hit.payload["chunk_index"] = parent_chunk[0]["chunk_index"]
            payload = hit.payload or {}
            result = {
                "text": payload.get("text"),
                "url": payload.get("url"),
                "title": payload.get("title"),
                "project_id": payload.get("project_id"),
                "strategy": payload.get("strategy"),
                "chunk_index": payload.get("chunk_index"),
                "score": hit.score
            }
            results.append(result)
        return results
    


    