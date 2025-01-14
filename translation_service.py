from deep_translator import GoogleTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate
import logging
from typing import Tuple
import langdetect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.supported_languages = GoogleTranslator().get_supported_languages()
        
    def detect_language(self, text: str) -> str:
        """Detect the language of input text."""
        try:
            return langdetect.detect(text)
        except:
            return 'en'
    
    def is_malayalam_transliterated(self, text: str) -> bool:
        """
        Check if the text might be Malayalam written in English letters.
        This is a simple heuristic - you might want to improve it.
        """
        # Common Malayalam word endings and patterns
        malayalam_patterns = ['il', 'am', 'um', 'anu', 'aanu', 'alle', 'ille']
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in malayalam_patterns)
    
    async def translate_text(self, text: str, target_lang: str = 'en') -> Tuple[str, str]:
        """
        Translate text to target language and keep track of source language.
        Returns: (translated_text, source_language)
        """
        try:
            source_lang = self.detect_language(text)
            
            # If already in target language, return as is
            if source_lang == target_lang:
                return text, source_lang
            
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)
            return translated, source_lang
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text, 'en'
    
    def transliterate_malayalam(self, text: str, to_malayalam: bool = True) -> str:
        """
        Convert between Malayalam and English transliteration.
        """
        try:
            if to_malayalam:
                # Convert English text to Malayalam script
                return transliterate(text, sanscript.ITRANS, sanscript.MALAYALAM)
            else:
                # Convert Malayalam script to English
                return transliterate(text, sanscript.MALAYALAM, sanscript.ITRANS)
        except Exception as e:
            logger.error(f"Transliteration error: {e}")
            return text