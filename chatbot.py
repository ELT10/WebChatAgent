from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from typing import Dict, Optional
import logging
import os
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileResponseCache:
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_hours * 3600
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _key_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, key: str) -> Optional[Dict]:
        path = self._key_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if time.time() - data.get("ts", 0) > self.ttl_seconds:
                return None
            return data.get("value")
        except Exception:
            return None
    
    def set(self, key: str, value: Dict) -> None:
        path = self._key_path(key)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"ts": time.time(), "value": value}, f)
        except Exception:
            pass


class WebsiteChatbot:
    def __init__(self, 
                 vectorstore,
                 model: str = "gpt-5-nano",
                 fallback_model: str = "gpt-5-mini",
                 temperature: float = 0.7,
                 max_history_tokens: int = 2000,
                 memory_summarizer_model: str = "gpt-3.5-turbo",
                 retrieval_k: int = 3,
                 enable_caching: bool = True,
                 enable_compression: bool = True,
                 cache_ttl_hours: int = 24):
        
        # LLM with fallback
        try:
            # Some models (gpt-5-nano/mini) only support default temperature=1
            enforced_temp = 1 if model in ("gpt-5-nano", "gpt-5-mini") else temperature
            llm = ChatOpenAI(temperature=enforced_temp, model=model)
        except Exception:
            enforced_temp_fb = 1 if fallback_model in ("gpt-5-nano", "gpt-5-mini") else temperature
            llm = ChatOpenAI(temperature=enforced_temp_fb, model=fallback_model)
        self.llm = llm
        
        # Summary + recency memory
        # Dedicated summarizer LLM for memory to avoid tokenizer issues
        try:
            summarizer_llm = ChatOpenAI(temperature=0, model=memory_summarizer_model)
        except Exception:
            summarizer_llm = self.llm
        
        self.memory = ConversationSummaryBufferMemory(
            llm=summarizer_llm,
            max_token_limit=max_history_tokens,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Base retriever with k=3/fetch_k=6
        base_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": retrieval_k,
                "fetch_k": retrieval_k * 2,
                "lambda_mult": 0.7
            }
        )
        
        # Contextual compression using the same LLM
        if enable_compression:
            compressor = LLMChainExtractor.from_llm(self.llm)
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
        else:
            self.retriever = base_retriever
        
        # Concise prompt
        self.qa_template = """You're a helpful assistant. Answer based only on the context.
        
        Context:
        {context}
        
        History:
        {chat_history}
        
        Question: {question}
        
        Answer:"""
        
        self.qa_prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["context", "chat_history", "question"]
        )
        
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True,
            verbose=True
        )
        
        self.cache = FileResponseCache(ttl_hours=cache_ttl_hours) if enable_caching else None

    async def get_response(self, query: str) -> Dict:
        """Get a response from the chatbot for the given query."""
        try:
            cache_key = None
            if self.cache:
                cache_key = f"q:{query.strip().lower()}"
                cached = self.cache.get(cache_key)
                if cached:
                    return cached
            
            response = self.chain.invoke({"question": query})
            
            sources = []
            for doc in response.get("source_documents", []):
                if doc.metadata.get("source"):
                    source = doc.metadata["source"]
                    if source not in sources:
                        sources.append(source)
            
            result = {
                "answer": response.get("answer", ""),
                "sources": sources
            }
            
            if self.cache and cache_key:
                self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": []
            }
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.memory.clear() 