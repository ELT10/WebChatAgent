from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration class
class Config:
    WEBSITE_URL = os.getenv('BASE_URL', 'https://sreesuryaayurveda.com')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        if not cls.WEBSITE_URL:
            raise ValueError("WEBSITE_URL is not set in environment variables") 