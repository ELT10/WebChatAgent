from scraping_agents import WebScrapingAgent, VisualScrapingAgent
from data_processor import DataProcessingAgent
from chatbot import WebsiteChatbot
from config import Config
from translation_service import TranslationService
from prompt_generator import generate_system_prompt
from typing import List, Dict, Optional, AsyncGenerator
import logging
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotOrchestrator:
    def __init__(self, website_url: str):
        self.website_url = website_url
        self.web_scraper = WebScrapingAgent(website_url)
        self.visual_scraper = VisualScrapingAgent(website_url)
        self.processor = DataProcessingAgent(
            embedding_type=Config.EMBEDDING_TYPE,
            local_embedding_model=Config.LOCAL_EMBEDDING_MODEL,
            chunk_size=1000,
            chunk_overlap=200,
            enable_ai_enhancement=Config.ENABLE_AI_ENHANCEMENT,
            enhancement_model=Config.ENHANCEMENT_MODEL,
            openai_api_key=Config.OPENAI_API_KEY,
        )
        self.translator = TranslationService()
        self.chatbot: Optional[WebsiteChatbot] = None
        
    async def initialize(self, force_scrape: bool = False) -> None:
        """
        Initialize the chatbot system. Can reuse existing scraped data unless force_scrape is True.
        """
        try:
            if force_scrape or not self._check_existing_data():
                logger.info("Starting web scraping...")
                await self._perform_scraping()
            
            logger.info("Processing data and initializing chatbot...")
            vectorstore = await self.processor.process_data()
            
            # Generate personalized system prompt based on website content
            logger.info("Generating personalized system prompt...")
            system_prompt = generate_system_prompt()
            
            self.chatbot = WebsiteChatbot(
                vectorstore,
                model=Config.CHAT_MODEL,
                fallback_model=Config.FALLBACK_CHAT_MODEL,
                temperature=Config.TEMPERATURE,
                max_history_tokens=Config.MAX_HISTORY_TOKENS,
                memory_summarizer_model=Config.MEMORY_SUMMARIZER_MODEL,
                retrieval_k=Config.RETRIEVAL_K,
                enable_caching=Config.ENABLE_CACHING,
                enable_compression=Config.ENABLE_COMPRESSION,
                cache_ttl_hours=Config.CACHE_TTL_HOURS,
                system_prompt=system_prompt,
            )
            logger.info("Chatbot initialization complete!")
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise
            
    async def _perform_scraping(self) -> None:
        """Perform both web and visual scraping."""
        try:
            # Perform web scraping
            web_data = await self.web_scraper.scrape_site()
            with open("web_scraping_results.json", "w", encoding="utf-8") as f:
                json.dump(web_data, f, ensure_ascii=False, indent=2)
                
            # Perform visual scraping
            await self.visual_scraper.setup()
            visual_data = await self.visual_scraper.scrape_site()
            await self.visual_scraper.cleanup()
            
            with open("visual_scraping_results.json", "w", encoding="utf-8") as f:
                json.dump(visual_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
            
    def _check_existing_data(self) -> bool:
        """Check if scraped data already exists."""
        return (os.path.exists("web_scraping_results.json") and 
                os.path.exists("visual_scraping_results.json"))
    
    async def chat(self, query: str) -> Dict:
        """Process chat query and return response."""
        try:
            # Detect input language
            input_lang = self.translator.detect_language(query)
            logger.info(f"Detected language: {input_lang}")
            
            # Translate query to English for processing
            if input_lang != 'en':
                translated_query, _ = await self.translator.translate_text(query, target_lang='en')
                logger.info(f"Translated query: {translated_query}")
            else:
                translated_query = query
            
            # Get response from chatbot
            response = await self.chatbot.get_response(translated_query)
            
            # Handle response translation based on input language
            if input_lang == 'ml':
                # Translate to Malayalam script
                translated_answer, _ = await self.translator.translate_text(
                    response["answer"], 
                    target_lang='ml'
                )
                response["answer"] = translated_answer
                
            elif input_lang == 'manglish':
                logger.info("Converting response to Manglish...")
                # First translate to Malayalam
                ml_answer, _ = await self.translator.translate_text(
                    response["answer"], 
                    target_lang='ml'
                )
                logger.info(f"Malayalam translation: {ml_answer}")
                
                # Then convert Malayalam to Manglish
                manglish_answer = self.translator.transliterate_malayalam(
                    ml_answer, 
                    to_malayalam=False
                )
                logger.info(f"Final Manglish answer: {manglish_answer}")
                response["answer"] = manglish_answer
            
            return response
            
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return {
                "answer": "I apologize, but I encountered an error. Please try again.",
                "sources": []
            }
            
    async def chat_stream(self, query: str) -> AsyncGenerator[Dict, None]:
        """
        Process chat query and stream response.
        Only streams for English responses; non-English responses are returned as complete.
        """
        try:
            logger.info(f"🌍 chat_stream() called with query: '{query[:80]}...'")
            
            # Detect input language
            input_lang = self.translator.detect_language(query)
            logger.info(f"🌐 Detected language: {input_lang}")
            
            # Translate query to English for processing
            if input_lang != 'en':
                logger.info(f"🔄 Translating {input_lang} to English...")
                translated_query, _ = await self.translator.translate_text(query, target_lang='en')
                logger.info(f"✅ Translated query: {translated_query}")
            else:
                translated_query = query
                logger.info("✅ Query is in English, no translation needed")
            
            # If input is English, use streaming
            if input_lang == 'en':
                logger.info("🎬 Using STREAMING response for English query")
                chunk_counter = 0
                async for chunk in self.chatbot.get_response_stream(translated_query):
                    chunk_counter += 1
                    logger.info(f"📦 Yielding chunk #{chunk_counter}: type='{chunk.get('type')}', content_length={len(chunk.get('content', ''))} chars")
                    yield chunk
                logger.info(f"✅ Streaming complete! Total chunks yielded: {chunk_counter}")
            else:
                # For non-English, get full response and translate
                logger.info(f"📄 Using NON-STREAMING response for {input_lang} query")
                response = await self.chatbot.get_response(translated_query)
                logger.info(f"✅ Got response, length: {len(response['answer'])} chars")
                
                # Handle response translation based on input language
                if input_lang == 'ml':
                    logger.info("🔄 Translating response to Malayalam script...")
                    # Translate to Malayalam script
                    translated_answer, _ = await self.translator.translate_text(
                        response["answer"], 
                        target_lang='ml'
                    )
                    response["answer"] = translated_answer
                    logger.info(f"✅ Malayalam translation complete, length: {len(translated_answer)} chars")
                    
                elif input_lang == 'manglish':
                    logger.info("🔄 Converting response to Manglish...")
                    # First translate to Malayalam
                    ml_answer, _ = await self.translator.translate_text(
                        response["answer"], 
                        target_lang='ml'
                    )
                    logger.info(f"✅ Malayalam translation: {ml_answer[:100]}...")
                    
                    # Then convert Malayalam to Manglish
                    manglish_answer = self.translator.transliterate_malayalam(
                        ml_answer, 
                        to_malayalam=False
                    )
                    logger.info(f"✅ Manglish conversion complete: {manglish_answer[:100]}...")
                    response["answer"] = manglish_answer
                
                # Return as single complete chunk
                logger.info(f"📦 Yielding single 'done' chunk with {len(response['sources'])} sources")
                yield {
                    "type": "done",
                    "content": response["answer"],
                    "sources": response["sources"]
                }
            
        except Exception as e:
            logger.error(f"❌ Error during chat stream: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": "I apologize, but I encountered an error. Please try again.",
                "sources": []
            }
            logger.info("📦 Yielded error message")
    
    def clear_chat_history(self) -> None:
        """Clear the chatbot's conversation history."""
        if self.chatbot:
            self.chatbot.memory.clear() 