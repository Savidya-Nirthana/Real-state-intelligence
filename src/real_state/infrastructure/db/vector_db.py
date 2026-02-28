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
    EMBEDDING_DIM
)

from typing import Dict, Any, List, Optional

class QdrantStorage:
    def __init__(self, url: str = None, api: str = None ,collection: str = 'crawl_data', timeout=30 ,dim=1536):
        self.embedding_dim = dim or EMBEDDING_DIM
        self.collection = collection or QDRANT_COLLECTION_NAME
        self.url = url or QDRANT_URL
        self.api = api or QDRANT_API_KEY
        self.timeout = timeout or QDRANT_TIMEOUT
        self.embedding = get_default_embedding()

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

    def upsert(self, 
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        collection_name: str = QDRANT_COLLECTION_NAME,
        batch_size: int = 100
    ) -> int:
        pass


    def search(self, 
        query_vector: List[float],
        top_k: int = 4,
        score_threshold: float = 0.0,
        collecion_name: str = QDRANT_COLLECTION_NAME,
        strategy_filter: Optional[str] = None
    ):
        pass
    


    