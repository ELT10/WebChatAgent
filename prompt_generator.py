"""
Dynamic System Prompt Generator

This module analyzes website content to automatically generate personalized
chatbot system prompts that reflect the business/organization context.
"""

from typing import Dict, List, Optional
import json
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Generates context-aware system prompts based on website content analysis.
    """
    
    # Keywords for identifying business types
    BUSINESS_TYPE_KEYWORDS = {
        'clinic': ['clinic', 'hospital', 'medical', 'health', 'treatment', 'doctor', 'patient'],
        'restaurant': ['restaurant', 'cafe', 'menu', 'food', 'dining', 'cuisine', 'chef'],
        'hotel': ['hotel', 'resort', 'accommodation', 'rooms', 'stay', 'booking', 'guest'],
        'ayurveda': ['ayurveda', 'ayurvedic', 'wellness', 'holistic', 'panchakarma', 'dosha'],
        'retail': ['shop', 'store', 'buy', 'purchase', 'products', 'sale', 'shopping'],
        'education': ['school', 'college', 'university', 'course', 'learning', 'education', 'student'],
        'spa': ['spa', 'massage', 'relaxation', 'therapy', 'wellness', 'beauty'],
        'fitness': ['gym', 'fitness', 'workout', 'training', 'exercise', 'yoga'],
    }
    
    @staticmethod
    def _extract_business_name(scraped_data: List[Dict]) -> Optional[str]:
        """Extract the business name from website data."""
        if not scraped_data:
            return None
            
        # Try to get from homepage title
        homepage = scraped_data[0] if scraped_data else None
        if homepage and homepage.get('title'):
            title = homepage['title']
            # Remove common suffixes
            business_name = re.sub(r'\s*[-|–]\s*(Home|Homepage|Welcome).*$', '', title, flags=re.IGNORECASE)
            business_name = re.sub(r'\s*[-|–]\s*[A-Z][a-z]+,\s*[A-Z][a-z]+.*$', '', business_name)  # Remove location
            return business_name.strip()
        
        return None
    
    @staticmethod
    def _identify_business_type(scraped_data: List[Dict]) -> str:
        """Identify the type of business based on content."""
        # Combine all text from first few pages for analysis
        combined_text = ""
        for item in scraped_data[:5]:  # Analyze first 5 pages
            combined_text += f" {item.get('title', '')} "
            combined_text += f" {item.get('main_content', '')} "
            for heading in item.get('headings', []):
                combined_text += f" {heading.get('text', '')} "
        
        combined_text = combined_text.lower()
        
        # Count keyword matches for each business type
        type_scores = {}
        for business_type, keywords in PromptGenerator.BUSINESS_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            type_scores[business_type] = score
        
        # Return the type with highest score
        if type_scores:
            identified_type = max(type_scores.items(), key=lambda x: x[1])
            if identified_type[1] > 0:  # At least one keyword match
                return identified_type[0]
        
        return 'general'
    
    @staticmethod
    def _extract_services_or_offerings(scraped_data: List[Dict]) -> List[str]:
        """Extract key services or offerings from the website."""
        services = []
        
        for item in scraped_data[:10]:  # Check first 10 pages
            headings = item.get('headings', [])
            for heading in headings:
                # Look for h2 and h3 headings which often contain service names
                if heading.get('level') in ['h2', 'h3']:
                    text = heading.get('text', '').strip()
                    # Filter out common navigation/generic headings
                    if text and len(text) < 100 and not any(
                        x in text.lower() for x in [
                            'about', 'contact', 'home', 'menu', 'blog', 
                            'gallery', 'testimonial', 'read more', 'learn more'
                        ]
                    ):
                        services.append(text)
        
        # Return unique services, limited to first 10
        return list(dict.fromkeys(services))[:10]
    
    @staticmethod
    def _extract_specialization(scraped_data: List[Dict], business_type: str) -> Optional[str]:
        """Extract business specialization from content."""
        if not scraped_data:
            return None
        
        homepage = scraped_data[0]
        
        # Look for common specialization indicators in headings
        for heading in homepage.get('headings', []):
            if heading.get('level') == 'h1':
                text = heading.get('text', '')
                # Extract phrases like "for Women", "for Kids", etc.
                match = re.search(r'\bfor\s+(\w+)', text, re.IGNORECASE)
                if match:
                    return match.group(1)
                # Look for other specialization patterns
                if any(word in text.lower() for word in ['specialist', 'specialized', 'expert']):
                    return text
        
        return None
    
    @staticmethod
    def generate_system_prompt(
        scraped_data_path: str = 'web_scraping_results.json',
        fallback_name: str = "this business"
    ) -> str:
        """
        Generate a personalized system prompt based on website content.
        
        Args:
            scraped_data_path: Path to the JSON file with scraped website data
            fallback_name: Fallback business name if extraction fails
            
        Returns:
            A personalized system prompt string
        """
        try:
            # Load scraped data
            with open(scraped_data_path, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            if not scraped_data:
                logger.warning("No scraped data found, using generic prompt")
                return PromptGenerator._get_generic_prompt()
            
            # Extract information
            business_name = PromptGenerator._extract_business_name(scraped_data) or fallback_name
            business_type = PromptGenerator._identify_business_type(scraped_data)
            specialization = PromptGenerator._extract_specialization(scraped_data, business_type)
            services = PromptGenerator._extract_services_or_offerings(scraped_data)
            
            logger.info(f"Detected business: {business_name} (Type: {business_type})")
            logger.info(f"Specialization: {specialization}")
            logger.info(f"Services found: {len(services)}")
            
            # Generate prompt based on business type
            prompt = PromptGenerator._generate_typed_prompt(
                business_name=business_name,
                business_type=business_type,
                specialization=specialization,
                services=services
            )
            
            logger.info(f"Generated system prompt: {prompt[:100]}...")
            return prompt
            
        except FileNotFoundError:
            logger.error(f"Scraped data file not found: {scraped_data_path}")
            return PromptGenerator._get_generic_prompt()
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return PromptGenerator._get_generic_prompt()
    
    @staticmethod
    def _generate_typed_prompt(
        business_name: str,
        business_type: str,
        specialization: Optional[str],
        services: List[str]
    ) -> str:
        """Generate a prompt based on identified business type."""
        
        # Base structure
        intro = f"You are a helpful virtual assistant for {business_name}"
        
        # Add type-specific context
        type_context = ""
        if business_type == 'ayurveda':
            type_context = ", an Ayurvedic wellness center"
            if specialization:
                type_context += f" specializing in care for {specialization.lower()}"
            closing = "Provide helpful information about Ayurvedic treatments, wellness services, and holistic health."
            
        elif business_type == 'clinic':
            type_context = ", a healthcare clinic"
            if specialization:
                type_context += f" specializing in {specialization.lower()}"
            closing = "Provide helpful information about medical services, treatments, and healthcare offerings."
            
        elif business_type == 'restaurant':
            type_context = ", a restaurant"
            closing = "Provide helpful information about menu items, dining options, and services."
            
        elif business_type == 'hotel':
            type_context = ", a hotel/accommodation"
            closing = "Provide helpful information about rooms, amenities, and booking services."
            
        elif business_type == 'spa':
            type_context = ", a spa and wellness center"
            closing = "Provide helpful information about spa treatments, wellness services, and relaxation offerings."
            
        elif business_type == 'education':
            type_context = ", an educational institution"
            closing = "Provide helpful information about courses, programs, and educational services."
            
        elif business_type == 'fitness':
            type_context = ", a fitness center"
            closing = "Provide helpful information about workout programs, training services, and fitness offerings."
            
        elif business_type == 'retail':
            type_context = ", a retail business"
            closing = "Provide helpful information about products, services, and shopping options."
            
        else:  # general
            closing = "Provide helpful information about services and offerings."
        
        # Construct the full prompt
        prompt = f"""{intro}{type_context}. Your role is to assist visitors by answering their questions accurately and professionally.

Your knowledge is strictly limited to the context provided below. If asked about something not covered in the context, politely inform the visitor that you don't have that information and suggest they contact the business directly.

{closing} Be professional yet friendly, and always aim to be helpful while staying within the boundaries of the provided information.

Context: {{context}}

History: {{chat_history}}

Question: {{question}}

Answer:"""
        
        return prompt
    
    @staticmethod
    def _get_generic_prompt() -> str:
        """Return a generic prompt when analysis fails."""
        return """You are a helpful virtual assistant. Your role is to assist visitors by answering their questions accurately and professionally.

Your knowledge is strictly limited to the context provided below. If asked about something not covered in the context, politely inform the visitor that you don't have that information.

Be professional yet friendly, and always aim to be helpful while staying within the boundaries of the provided information.

Context: {context}

History: {chat_history}

Question: {question}

Answer:"""


# Convenience function for easy import
def generate_system_prompt(scraped_data_path: str = 'web_scraping_results.json') -> str:
    """Generate a personalized system prompt based on website content."""
    return PromptGenerator.generate_system_prompt(scraped_data_path)

