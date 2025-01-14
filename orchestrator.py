from scraping_agents import WebScrapingAgent, VisualScrapingAgent
from data_processor import DataProcessingAgent
from chatbot import WebsiteChatbot
from translation_service import TranslationService
from typing import List, Dict, Optional
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
        self.processor = DataProcessingAgent()
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
            self.chatbot = WebsiteChatbot(vectorstore)
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
        """
        Handle chat with translation support.
        """
        if not self.chatbot:
            raise RuntimeError("Chatbot not initialized. Please call initialize() first.")
            
        try:
            # Handle potential Malayalam transliteration
            if self.translator.is_malayalam_transliterated(query):
                query = self.translator.transliterate_malayalam(query, to_malayalam=True)
            
            # Translate query to English
            english_query, source_lang = await self.translator.translate_text(query, target_lang='en')
            
            # Get response from chatbot
            response = await self.chatbot.get_response(english_query)
            
            # Translate response back to source language if not English
            if source_lang != 'en':
                translated_answer, _ = await self.translator.translate_text(
                    response["answer"], 
                    target_lang="en"
                )
                response["answer"] = translated_answer
                
                # If original query was transliterated Malayalam, convert response to English script
                if self.translator.is_malayalam_transliterated(query):
                    response["answer"] = self.translator.transliterate_malayalam(
                        response["answer"], 
                        to_malayalam=False
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return {
                "answer": "I apologize, but I encountered an error. Please try again.",
                "sources": []
            }
            
    def clear_chat_history(self) -> None:
        """Clear the chatbot's conversation history."""
        if self.chatbot:
            self.chatbot.clear_history() 