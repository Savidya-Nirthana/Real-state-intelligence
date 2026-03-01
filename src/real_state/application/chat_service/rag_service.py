from typing import Any, Dict, List
import time


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, Runnable
from real_state.infrastructure.db.vector_db import QdrantStorage

from real_state.config import TOP_K_RESULTS
from real_state.application.domain.prompts.rag_template import RAG_TEMPLATE
from real_state.application.domain.utils import format_docs

def build_rag_chain(
    llm : Any,
    template: str = RAG_TEMPLATE,
)-> Runnable:
    """
    Build modern RAG chain using Langchain Expression language(LCEL).
    """
    
    rag_prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        rag_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

class RagService:
    def __init__(
        self, 
        llm: Any,
        k: int = TOP_K_RESULTS,
        retriever: Any = QdrantStorage(),
    ):
        """
        Initialize RAG service.

        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm
        self.retriever = retriever
        self.chain = build_rag_chain(llm)
        self.k = k

    def generate(self, query: str) -> Dict[str, Any]:
        """
        Generate answer for query using RAG.

        Args:
            query: User question
        
        Returns:
            Dict with:
            - answer: Generated answer string
            - evidence: List of retrieved documents
            - evidence_urls: List of unique source URLS
            - generation_time: 

        """
        start = time.time()
        
        evidence = self.retriever.search_chunks(query=query, top_k=self.k)

        answer = self.chain.invoke({"context" : format_docs(evidence), "question" : query})

        elapsed = time.time() - start

        evidence_urls = list(set([doc.get('url') for doc in evidence]))

        return {
            'answer' : answer,
            'evidence' : evidence,
            'evidence_urls' : evidence_urls,
            'generation_time' : elapsed,
            'num_docs' : len(evidence)
        }

    
    def stream(self, query: str): 
        """
        Generate answers for multiple

        Args:
            queries: User question

        Yields:
            String chunks as they're generated
        """
        for chunk in self.chain.stream(query):
            yield 
            

    def batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Generated answers for multiple queries in batch.

        Args:
            queries: List of user questions

        Returns:
            List of result dicts (same format as generate())
        """
        results = []
        for query in queries:
            results.append(self.generate(query))
        return results
    


__all__ = [
    "build_rag_chain",
    "RagService"
]

        
    

    

