from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
import json
import os
from typing import List, Dict
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessingAgent:
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 persist_directory: str = "./data/chroma_db"):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = persist_directory
        
    def _load_json_data(self, filename: str) -> List[Dict]:
        """Load data from JSON file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []

    def _combine_scraped_data(self) -> List[Dict]:
        """Combine data from both web scraping and visual scraping."""
        web_data = self._load_json_data("web_scraping_results.json")
        visual_data = self._load_json_data("visual_scraping_results.json")
        
        # Handle case where visual_data is a single dictionary
        if isinstance(visual_data, dict):
            visual_data = [visual_data]
            
        return web_data + visual_data

    def _prepare_documents(self, data: List[Dict]) -> List[Document]:
        """Split text into chunks and prepare documents."""
        documents = []
        for item in data:
            if not item.get('content'):
                continue
                
            chunks = self.text_splitter.split_text(item['content'])
            documents.extend([
                Document(
                    page_content=chunk,
                    metadata={
                        "source": item['url'],
                        "chunk_type": "text"
                    }
                ) for chunk in chunks
            ])
        return documents

    async def process_data(self) -> Chroma:
        """Process scraped data and create vector store."""
        logger.info("Starting data processing...")
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Load and combine data
        combined_data = self._combine_scraped_data()
        if not combined_data:
            raise ValueError("No data found to process")
            
        # Prepare documents
        documents = self._prepare_documents(combined_data)
        logger.info(f"Prepared {len(documents)} document chunks")
        
        # Create and persist vector store
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        vectorstore.persist()
        
        logger.info("Data processing completed and vector store created")
        return vectorstore 