"""
AI-powered content enhancement for generalized web scraping.
Cleans, structures, and adds context to scraped content.
"""

import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentEnhancer:
    """
    Enhances raw scraped content using AI to improve retrieval quality.
    Designed for generalized websites with varying data quality.
    """
    
    def __init__(
        self, 
        model: str = "gpt-4o-mini",  # Cheap but effective
        max_concurrent: int = 5,      # Process 5 pages at once
        api_key: Optional[str] = None
    ):
        self.model = model
        self.max_concurrent = max_concurrent
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info(f"ContentEnhancer initialized with model: {model}")
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _enhance_single_page(self, page_data: Dict) -> Dict:
        """Enhance a single page's content using AI."""
        
        prompt = self._build_enhancement_prompt(page_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a content processing assistant for a chatbot system.
Your job is to clean and structure web scraped content for better information retrieval.

RULES:
1. Remove navigation elements (Learn More, Click Here, etc.)
2. Fix obvious typos and formatting issues
3. Add contextual information that's implicit in the page structure
4. DO NOT invent information - only work with what's given
5. DO NOT summarize - preserve all factual content
6. DO NOT change meaning - only improve clarity
7. Structure the content with clear sections

IMPORTANT: You must respond with valid JSON only. Return your response in this exact JSON format:
{
  "title": "Clear page title",
  "business_context": "What business/entity this page is about",
  "content_type": "Type of content (service, product, article, about, contact, etc.)",
  "main_content": "Cleaned and structured content with clear sections as a PLAIN TEXT STRING (not nested objects)",
  "key_information": ["List", "of", "key", "facts", "or", "entities"]
}

CRITICAL: The "main_content" field must be a plain text string with newlines, NOT a nested JSON object or dictionary."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )
            
            enhanced = json.loads(response.choices[0].message.content)
            
            # Merge enhanced content back into original structure
            page_data['enhanced'] = True
            page_data['title'] = enhanced.get('title', page_data.get('title', ''))
            page_data['business_context'] = enhanced.get('business_context', '')
            page_data['content_type'] = enhanced.get('content_type', 'general')
            page_data['main_content'] = enhanced.get('main_content', page_data.get('main_content', ''))
            page_data['key_information'] = enhanced.get('key_information', [])
            
            logger.info(f"✅ Enhanced: {page_data['url']}")
            return page_data
            
        except Exception as e:
            logger.error(f"❌ Error enhancing {page_data.get('url')}: {e}")
            # Return original if enhancement fails
            page_data['enhanced'] = False
            return page_data
    
    def _build_enhancement_prompt(self, page_data: Dict) -> str:
        """Build a prompt for content enhancement."""
        parts = []
        
        parts.append(f"URL: {page_data.get('url', 'unknown')}")
        parts.append(f"Page Title: {page_data.get('title', 'untitled')}")
        
        if page_data.get('metadata', {}).get('description'):
            parts.append(f"Meta Description: {page_data['metadata']['description']}")
        
        if page_data.get('headings'):
            headings = [h['text'] for h in page_data['headings'][:10]]
            parts.append(f"Headings: {', '.join(headings)}")
        
        # Limit content length to avoid token overflow
        content = page_data.get('main_content', '')[:3000]
        parts.append(f"\nContent to enhance:\n{content}")
        parts.append("\nPlease clean, structure, and enhance this content following the rules.")
        
        return "\n".join(parts)
    
    async def enhance_batch(self, pages: List[Dict]) -> List[Dict]:
        """Enhance multiple pages concurrently."""
        logger.info(f"🚀 Enhancing {len(pages)} pages using {self.model}...")
        
        enhanced_pages = []
        
        # Process in batches to respect rate limits
        for i in range(0, len(pages), self.max_concurrent):
            batch = pages[i:i + self.max_concurrent]
            batch_num = i // self.max_concurrent + 1
            total_batches = (len(pages) - 1) // self.max_concurrent + 1
            logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} pages)")
            
            tasks = [self._enhance_single_page(page.copy()) for page in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch error: {result}")
                else:
                    enhanced_pages.append(result)
            
            # Small delay between batches to avoid rate limits
            if i + self.max_concurrent < len(pages):
                await asyncio.sleep(0.5)
        
        success_count = sum(1 for p in enhanced_pages if p.get('enhanced'))
        logger.info(f"✅ Enhanced {success_count}/{len(pages)} pages successfully")
        
        return enhanced_pages
    
    def estimate_cost(
        self, 
        pages: List[Dict], 
        input_cost_per_1m: float = 0.15,  # GPT-4o-mini pricing
        output_cost_per_1m: float = 0.60
    ) -> Dict:
        """Estimate the cost of enhancing the given pages."""
        
        # Rough token estimation (1 token ≈ 4 characters)
        total_input_tokens = 0
        system_prompt_tokens = 150  # Approximate system prompt size
        
        for page in pages:
            # Calculate tokens for this page
            content_length = len(str(page.get('main_content', '')))
            title_length = len(str(page.get('title', '')))
            meta_length = len(str(page.get('metadata', {}).get('description', '')))
            
            # Estimate tokens (text length / 4 + overhead)
            page_tokens = (content_length + title_length + meta_length) // 4 + system_prompt_tokens + 100
            total_input_tokens += page_tokens
        
        # Assume output is ~40% of input (structured but comprehensive)
        total_output_tokens = int(total_input_tokens * 0.4)
        
        input_cost = (total_input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (total_output_tokens / 1_000_000) * output_cost_per_1m
        total_cost = input_cost + output_cost
        
        return {
            "estimated_input_tokens": total_input_tokens,
            "estimated_output_tokens": total_output_tokens,
            "estimated_cost_usd": round(total_cost, 3),
            "pages_count": len(pages),
            "cost_per_page": round(total_cost / len(pages), 4) if pages else 0,
            "model": self.model
        }
    
    @staticmethod
    def needs_enhancement(page: Dict) -> bool:
        """
        Determine if a page needs AI enhancement.
        Can be used for selective enhancement to reduce costs.
        """
        content = page.get('main_content', '')
        
        # Always enhance if content is very short
        if len(content) < 200:
            return True
        
        # Enhance if lots of navigation noise
        navigation_keywords = ['Learn More', 'Click Here', 'Read More', 'View More']
        noise_count = sum(content.count(keyword) for keyword in navigation_keywords)
        if noise_count > 3:
            return True
        
        # Enhance if lots of special characters (poor scraping quality)
        special_chars = '★►•◄→←↑↓'
        noise_ratio = sum(1 for c in content if c in special_chars) / max(len(content), 1)
        if noise_ratio > 0.05:
            return True
        
        # Enhance if content seems to be just a list without context
        lines = content.split('\n')
        short_lines = [l for l in lines if len(l.strip()) < 50]
        if len(short_lines) > len(lines) * 0.7:  # More than 70% short lines
            return True
        
        return False

