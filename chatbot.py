from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from typing import Dict, Optional, AsyncGenerator
from openai import AsyncOpenAI
import logging
import os
import time
import json
import asyncio
from functools import partial

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
                 cache_ttl_hours: int = 24,
                 system_prompt: Optional[str] = None):
        
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
        
        # Use provided system prompt or default
        if system_prompt:
            self.qa_template = system_prompt
            logger.info("Using custom system prompt")
        else:
            self.qa_template = """You're a helpful assistant. Answer based only on the context.
        
        Context:
        {context}
        
        History:
        {chat_history}
        
        Question: {question}
        
        Answer:"""
            logger.info("Using default system prompt")
        
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
        
        # Initialize async OpenAI client for streaming
        try:
            self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            # Check if Responses API is available
            has_responses = hasattr(self.openai_client, 'responses')
            if has_responses:
                logger.info("✅ OpenAI Responses API available for streaming")
            else:
                logger.warning("⚠️ OpenAI Responses API not available - will use fallback")
                logger.warning("📦 Consider upgrading: pip install --upgrade openai")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None

    async def get_response(self, query: str, language_instruction: Optional[str] = None) -> Dict:
        """Get a response from the chatbot for the given query."""
        try:
            cache_key = None
            if self.cache:
                cache_key = f"q:{query.strip().lower()}"
                cached = self.cache.get(cache_key)
                if cached:
                    return cached
            
            # Add language instruction to the query if provided
            if language_instruction:
                query_with_instruction = f"{query}\n\n{language_instruction}"
            else:
                query_with_instruction = query
            
            response = self.chain.invoke({"question": query_with_instruction})
            
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
    
    async def get_response_stream(self, query: str, language_instruction: Optional[str] = None) -> AsyncGenerator[Dict, None]:
        """
        Get a streaming response from the chatbot using OpenAI Responses API.
        This method yields chunks of the response as they arrive.
        """
        try:
            logger.info(f"🔍 Starting streaming response for query: '{query[:80]}...'")
            if language_instruction:
                logger.info(f"🌐 Language instruction: {language_instruction}")
            
            # First, retrieve relevant context from the vectorstore
            logger.info("📚 Retrieving relevant documents from vectorstore...")
            # Run sync retrieval in thread executor to avoid blocking
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None, 
                self.retriever.get_relevant_documents, 
                query
            )
            logger.info(f"📚 Retrieved {len(docs)} documents")
            
            # Format context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Get chat history (run sync operation in thread executor)
            chat_history_dict = await loop.run_in_executor(
                None,
                self.memory.load_memory_variables,
                {}
            )
            chat_history = chat_history_dict.get("chat_history", [])
            history_text = ""
            if chat_history:
                for msg in chat_history[-4:]:  # Last 4 messages for context
                    role = msg.type if hasattr(msg, 'type') else 'user'
                    content = msg.content if hasattr(msg, 'content') else str(msg)
                    history_text += f"{role}: {content}\n"
            
            # Prepare instructions (similar to the prompt template)
            instructions = f"""You're a helpful assistant. Answer based only on the context provided.

Context:
{context}

Chat History:
{history_text}

Answer the user's question naturally and helpfully."""
            
            # Add language instruction if provided
            if language_instruction:
                instructions += f"\n\nIMPORTANT: {language_instruction}"
            
            # Extract sources for later
            sources = []
            for doc in docs:
                if doc.metadata.get("source"):
                    source = doc.metadata["source"]
                    if source not in sources:
                        sources.append(source)
            
            # Stream response using OpenAI Responses API
            logger.info(f"🤖 Calling OpenAI Responses API (model: {self.llm.model_name})...")
            logger.info(f"📊 Context length: {len(context)} chars, History length: {len(history_text)} chars")
            
            try:
                # Check if OpenAI client was initialized
                if self.openai_client is None:
                    logger.error("❌ OpenAI client not initialized!")
                    raise AttributeError("OpenAI client is None")
                
                # Check if responses API exists
                if not hasattr(self.openai_client, 'responses'):
                    logger.error("❌ OpenAI client does not have 'responses' attribute!")
                    logger.error("📦 Please upgrade: pip install --upgrade openai")
                    raise AttributeError("Responses API not available")
                
                logger.info("✅ Responses API available, creating stream...")
                response_stream = await self.openai_client.responses.create(
                    model=self.llm.model_name,
                    instructions=instructions,
                    input=query,
                    stream=True
                )
                
                full_answer = ""
                
                # Process stream events
                chunk_count = 0
                async for event in response_stream:
                    event_type = event.type if hasattr(event, 'type') else None
                    logger.debug(f"Received event type: {event_type}")
                    
                    # Extract text delta from the event
                    if event_type == "response.output_text.delta":
                        delta = event.delta if hasattr(event, 'delta') else ""
                        if delta:
                            chunk_count += 1
                            full_answer += delta
                            logger.info(f"📤 Chunk #{chunk_count}: '{delta[:50]}{'...' if len(delta) > 50 else ''}' (length: {len(delta)})")
                            yield {
                                "type": "chunk",
                                "content": delta
                            }
                    
                    elif event_type == "response.output_text.done":
                        # Final text is available
                        text = event.text if hasattr(event, 'text') else full_answer
                        full_answer = text
                        logger.info(f"✅ Streaming completed! Total chunks: {chunk_count}, Full answer length: {len(full_answer)}")
                        logger.info(f"📝 First 100 chars: {full_answer[:100]}...")
                
                # Save to memory
                logger.info("💾 Saving conversation to memory...")
                # Run sync memory operation in thread executor
                await loop.run_in_executor(
                    None,
                    self.memory.save_context,
                    {"input": query},
                    {"answer": full_answer}
                )
                
                # Yield final message with sources
                logger.info(f"🏁 Sending final 'done' message with {len(sources)} sources")
                yield {
                    "type": "done",
                    "content": full_answer,
                    "sources": sources
                }
                
            except AttributeError as e:
                # Fallback if responses API is not available
                logger.warning(f"⚠️ Responses API not available, falling back to standard response: {e}")
                logger.info("🔄 Using LangChain chat completion instead...")
                result = await self.get_response(query, language_instruction=language_instruction)
                logger.info(f"✅ Fallback response received, length: {len(result['answer'])} chars")
                yield {
                    "type": "done",
                    "content": result["answer"],
                    "sources": result["sources"]
                }
            except Exception as api_error:
                # Handle any other API errors
                logger.error(f"❌ Error calling Responses API: {api_error}", exc_info=True)
                logger.info("🔄 Falling back to standard response...")
                result = await self.get_response(query, language_instruction=language_instruction)
                logger.info(f"✅ Fallback response received, length: {len(result['answer'])} chars")
                yield {
                    "type": "done",
                    "content": result["answer"],
                    "sources": result["sources"]
                }
                
        except Exception as e:
            logger.error(f"❌ Error generating streaming response: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": []
            }
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.memory.clear() 