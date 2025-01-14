from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
import json
import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessingAgent:
    def __init__(self, 
                 chunk_size: int = 1000,  # Increased chunk size for better context
                 chunk_overlap: int = 200,  # Increased overlap
                 persist_directory: str = "./data/chroma_db"):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = persist_directory

    def _create_structured_content(self, item: Dict) -> str:
        """Create well-structured content from a page item."""
        content_parts = []
        
        # Add title
        if item.get('title'):
            content_parts.append(f"Page: {item['title']}")
        
        # Add description from metadata if available
        if item.get('metadata', {}).get('description'):
            content_parts.append(f"Description: {item['metadata']['description']}")
        
        # Process headings hierarchically
        if item.get('headings'):
            current_section = []
            for heading in item['headings']:
                level = int(heading['level'].replace('h', ''))
                text = heading['text']
                current_section = current_section[:level-1] + [text]
                content_parts.append(f"Section {' > '.join(current_section)}")
        
        # Add main content with proper context
        if item.get('main_content'):
            content_parts.append(f"Content: {item['main_content']}")
            
        return "\n\n".join(content_parts)

    def _clean_metadata(self, metadata: Dict) -> Dict:
        """Clean metadata to ensure only simple types are stored."""
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                cleaned[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Convert dicts to string representation
                cleaned[key] = str(value)
            elif value is None:
                cleaned[key] = ""
            else:
                # Convert any other types to string
                cleaned[key] = str(value)
        return cleaned

    def _prepare_documents(self, scraped_data: List[Dict]) -> List[Document]:
        """Prepare documents with better structure and metadata."""
        documents = []
        
        for item in scraped_data:
            # Skip error pages or empty content
            if "page not found" in item.get('title', '').lower():
                continue
                
            # Create structured content
            structured_content = self._create_structured_content(item)
            
            # Clean metadata
            clean_metadata = self._clean_metadata({
                'source': item['url'],
                'title': item.get('title', ''),
                'type': 'content',
                'description': item.get('metadata', {}).get('description', ''),
                'sections': [h['text'] for h in item.get('headings', [])],
                'page_type': item.get('metadata', {}).get('og:type', 'page')
            })
            
            # Split content into chunks while maintaining context
            chunks = self.text_splitter.split_text(structured_content)
            
            for chunk in chunks:
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata=clean_metadata
                    )
                )
        
        return documents

    async def process_data(self) -> Chroma:
        """Process scraped data and create vector store."""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Load scraped data
            with open('web_scraping_results.json', 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            if not scraped_data:
                raise ValueError("No data found to process")
            
            # Prepare documents
            documents = self._prepare_documents(scraped_data)
            logger.info(f"Prepared {len(documents)} documents")
            
            # Create and persist vector store
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            vectorstore.persist()
            
            return vectorstore
            
        except Exception as e:
            logger.error(f"Error during data processing: {e}")
            raise 