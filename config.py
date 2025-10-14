from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration class
class Config:
    WEBSITE_URL = os.getenv('BASE_URL', 'https://sreesuryaayurveda.com')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Chat model configuration
    CHAT_MODEL = os.getenv('CHAT_MODEL', 'gpt-5-nano')
    FALLBACK_CHAT_MODEL = os.getenv('FALLBACK_CHAT_MODEL', 'gpt-5-mini')
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
    MAX_HISTORY_TOKENS = int(os.getenv('MAX_HISTORY_TOKENS', '2000'))
    MEMORY_SUMMARIZER_MODEL = os.getenv('MEMORY_SUMMARIZER_MODEL', 'gpt-3.5-turbo')
    
    # Retrieval and compression
    RETRIEVAL_K = int(os.getenv('RETRIEVAL_K', '3'))
    ENABLE_COMPRESSION = os.getenv('ENABLE_COMPRESSION', 'true').strip().lower() in ('1', 'true', 'yes', 'y')
    
    # Caching
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').strip().lower() in ('1', 'true', 'yes', 'y')
    CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '24'))
    
    # Embeddings
    EMBEDDING_TYPE = os.getenv('EMBEDDING_TYPE', 'local').strip().lower()  # 'local' or 'openai'
    LOCAL_EMBEDDING_MODEL = os.getenv('LOCAL_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        if not cls.WEBSITE_URL:
            raise ValueError("WEBSITE_URL is not set in environment variables") 