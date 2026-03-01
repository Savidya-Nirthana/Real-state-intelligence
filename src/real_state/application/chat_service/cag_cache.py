import hashlib
import pickle
import time
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime



class CAGCache:
    def __init__(
        self,
        cache_dir: Path,
        embedder: Any,
        similarity_threshold: float = 0.90,
        max_cache_size: int = 1000,
        history_ttl_hours: float = 24.0
    ):
        """
            Intialize semantic cache

        """

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.history_ttl_hours = history_ttl_hours


        self.faq_cache_file = self.cache_dir / "cag_cache.pkl"
        self.history_cache_file = self.cache_dir / "cag_history.pkl"

        self.faq_cache: Dict[str, Any] = self._load_cache(self.faq_cache_file)
        self.history_cache: Dict[str, Any] = self._load_cache(self.history_cache_file)

        self._cleanup_expired_history()

        self._update_faq_embeddings_matrix()
        self._update_history_embeddings_matrix()



    def _load_cache(self, file_path: Path) -> Dict[str, Any]:
        """
            Load cache from file
        """
        if file_path.exists():
            try:
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                return {}
        return {}

    def _save_faq_cache(self)-> None:
        """
            Save cache to file
        """
        with open(self.faq_cache_file, "wb") as f:
            pickle.dump(self.faq_cache, f)
        
    def _save_history_cache(self)-> None:
        """
            Save cache to file
        """
        with open(self.history_cache_file, "wb") as f:
            pickle.dump(self.history_cache, f)

        
    def _cleanup_expired_history(self) -> None:
        """
            Remove expired history entries
        """
        cutoff_time = time.time() - (self.history_ttl_hours * 3600)

        expired_keys = [
            key for key, entry in self.history_cache.items()
            if entry["timestamp"] < cutoff_time
        ]

        if expired_keys:
            for key in expired_keys:
                del self.history_cache[key]
            self._save_history_cache()

    def _embed_query(self, query: str) -> np.ndarray:
        """
            Embed query
        """
        embedding = self.embedder.embed_query(query)
        return np.array(embedding)

    


