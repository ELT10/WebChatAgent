from deep_translator import GoogleTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import logging
from typing import Tuple
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.supported_languages = ['en', 'ml']
        # Common Manglish patterns
        self.manglish_patterns = [
            r'\b(aa|ee|oo|mm|nn|th|zh|ch|ll|rr|tt)\b',
            r'\b(nj|ng|nt)\b',
            r'[aeiou]{2,}',
            r'[a-z]+(?:kk|pp|tt|cc)[a-z]+',
            r'\b(um|nu|ku|thu|ru|lu)\b'
        ]
        
        # Malayalam to Manglish character mappings
        self.ml_to_manglish = {
            'അ': 'a', 'ആ': 'aa', 'ഇ': 'i', 'ഈ': 'ee', 
            'ഉ': 'u', 'ഊ': 'oo', 'ഋ': 'ri', 'എ': 'e',
            'ഏ': 'e', 'ഐ': 'ai', 'ഒ': 'o', 'ഓ': 'o',
            'ഔ': 'au', 'ക': 'k', 'ഖ': 'kh', 'ഗ': 'g',
            'ഘ': 'gh', 'ങ': 'ng', 'ച': 'ch', 'ഛ': 'chh',
            'ജ': 'j', 'ഝ': 'jh', 'ഞ': 'nj', 'ട': 't',
            'ഠ': 'th', 'ഡ': 'd', 'ഢ': 'dh', 'ണ': 'n',
            'ത': 'th', 'ഥ': 'th', 'ദ': 'd', 'ധ': 'dh',
            'ന': 'n', 'പ': 'p', 'ഫ': 'ph', 'ബ': 'b',
            'ഭ': 'bh', 'മ': 'm', 'യ': 'y', 'ര': 'r',
            'ല': 'l', 'വ': 'v', 'ശ': 'sh', 'ഷ': 'sh',
            'സ': 's', 'ഹ': 'h', 'ള': 'l', 'ഴ': 'zh',
            'റ': 'r', '്': '', 'ം': 'm', 'ഃ': 'h',
            'ാ': 'aa', 'ി': 'i', 'ീ': 'ee', 'ു': 'u',
            'ൂ': 'oo', 'ൃ': 'ri', 'െ': 'e', 'േ': 'e',
            'ൈ': 'ai', 'ൊ': 'o', 'ോ': 'o', 'ൌ': 'au',
            'ൗ': 'au', '़': '', 'ൺ': 'n', 'ൻ': 'n',
            'ർ': 'r', 'ൽ': 'l', 'ൾ': 'l', 'ൿ': 'k'
        }

    def _convert_to_manglish(self, malayalam_text: str) -> str:
        """Convert Malayalam text to Manglish using character mapping."""
        output = []
        i = 0
        text_length = len(malayalam_text)
        
        while i < text_length:
            char = malayalam_text[i]
            if char in self.ml_to_manglish:
                output.append(self.ml_to_manglish[char])
            else:
                output.append(char)
            i += 1
        
        manglish = ''.join(output)
        
        # Post-processing for better readability
        manglish = re.sub(r'([aeiou])\1+', r'\1', manglish)  # Remove repeated vowels
        manglish = re.sub(r'aa', 'a', manglish)  # Simplify 'aa' to 'a'
        manglish = re.sub(r'([^aeiou])\1+', r'\1', manglish)  # Remove repeated consonants
        
        return manglish

    async def translate_text(self, text: str, target_lang: str = 'en') -> Tuple[str, str]:
        """Translate text between English and Malayalam."""
        try:
            source_lang = self.detect_language(text)
            logger.info(f"Translating from {source_lang} to {target_lang}")
            
            if source_lang == target_lang:
                return text, source_lang
            
            # Handle Manglish input
            if source_lang == 'manglish':
                # First translate to English
                translator = GoogleTranslator(source='en', target='en')
                english_text = translator.translate(text)
                
                if target_lang == 'en':
                    return english_text, source_lang
                else:
                    # Then to Malayalam if needed
                    translator = GoogleTranslator(source='en', target='ml')
                    return translator.translate(english_text), source_lang
            
            # Regular translation
            translator = GoogleTranslator(
                source='ml' if source_lang == 'ml' else 'en',
                target='ml' if target_lang == 'ml' else 'en'
            )
            translated = translator.translate(text)
            logger.info(f"Translated text: {translated}")
            return translated, source_lang
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text, 'en'

    def detect_language(self, text: str) -> str:
        """Detect if text is English, Malayalam or Manglish."""
        try:
            # Check for Malayalam script
            if any('\u0D00' <= c <= '\u0D7F' for c in text):
                return 'ml'
            
            # Check for Manglish
            if self.is_malayalam_transliterated(text):
                logger.info("Detected as Manglish")
                return 'manglish'
            
            return 'en'
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'

    def is_malayalam_transliterated(self, text: str) -> bool:
        """Check if text appears to be Malayalam written in English (Manglish)."""
        text = text.lower()
        pattern_matches = sum(1 for pattern in self.manglish_patterns 
                            if re.search(pattern, text))
        return pattern_matches >= 2

    def transliterate_malayalam(self, text: str, to_malayalam: bool = True) -> str:
        """Convert between Malayalam and Manglish."""
        try:
            if to_malayalam:
                # Convert Manglish to Malayalam
                translator = GoogleTranslator(source='en', target='ml')
                return translator.translate(text)
            else:
                # Convert Malayalam to Manglish
                return self._convert_to_manglish(text)
                
        except Exception as e:
            logger.error(f"Transliteration error: {e}")
            return text