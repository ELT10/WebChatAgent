#!/usr/bin/env python3
"""
Test script for AI content enhancement feature.
Run this to see the enhancement in action with sample data.
"""

import asyncio
import json
from content_enhancer import ContentEnhancer
from dotenv import load_dotenv
import os

load_dotenv()

# Sample scraped data (messy/noisy content)
SAMPLE_DATA = [
    {
        "url": "https://example-clinic.com/services",
        "title": "Services - Health Clinic",
        "headings": [
            {"level": "h1", "text": "Our Services"},
            {"level": "h2", "text": "Treatments"},
            {"level": "h3", "text": "Acne"},
            {"level": "h3", "text": "Diabetes"},
        ],
        "main_content": """Our Services
        Learn More
        Acne
        Learn More
        Diabetes
        Learn More
        Hair Loss
        Learn More
        ★★★★★
        Great service!
        ★★★★★
        Highly recommend!
        Contact us
        Learn More""",
        "metadata": {
            "description": "We offer various health treatments and services for your wellness needs."
        }
    },
    {
        "url": "https://example-clinic.com/about",
        "title": "About Us",
        "headings": [
            {"level": "h1", "text": "About Our Clinic"},
        ],
        "main_content": """About Our Clinic
        Click Here
        We are a leading healthcare provider
        excercising the highest standards
        Read More
        Our team of experts
        View More
        Contact us today
        Learn More""",
        "metadata": {
            "description": "Learn more about our clinic and our team"
        }
    }
]


async def test_enhancement():
    """Test the enhancement feature with sample data."""
    
    print("=" * 70)
    print("🧪 AI CONTENT ENHANCEMENT TEST")
    print("=" * 70)
    print()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        return
    
    print(f"✅ OpenAI API Key found: {api_key[:10]}...")
    print()
    
    # Initialize enhancer
    enhancer = ContentEnhancer(
        model="gpt-4o-mini",
        api_key=api_key
    )
    
    print(f"📊 Sample Data: {len(SAMPLE_DATA)} pages")
    print()
    
    # Show original content
    print("📄 ORIGINAL CONTENT (BEFORE ENHANCEMENT)")
    print("-" * 70)
    for i, page in enumerate(SAMPLE_DATA, 1):
        print(f"\nPage {i}: {page['title']}")
        print(f"URL: {page['url']}")
        print(f"Content preview: {page['main_content'][:150]}...")
    print()
    
    # Estimate cost
    cost_estimate = enhancer.estimate_cost(SAMPLE_DATA)
    print("💰 COST ESTIMATE")
    print("-" * 70)
    print(f"Pages: {cost_estimate['pages_count']}")
    print(f"Model: {cost_estimate['model']}")
    print(f"Input tokens: ~{cost_estimate['estimated_input_tokens']:,}")
    print(f"Output tokens: ~{cost_estimate['estimated_output_tokens']:,}")
    print(f"Cost per page: ${cost_estimate['cost_per_page']}")
    print(f"Total cost: ${cost_estimate['estimated_cost_usd']}")
    print()
    
    # Enhance content
    print("🚀 ENHANCING CONTENT...")
    print("-" * 70)
    enhanced_data = await enhancer.enhance_batch(SAMPLE_DATA)
    print()
    
    # Show enhanced content
    print("✨ ENHANCED CONTENT (AFTER ENHANCEMENT)")
    print("-" * 70)
    for i, page in enumerate(enhanced_data, 1):
        print(f"\n{'=' * 70}")
        print(f"Page {i}: {page['title']}")
        print(f"{'=' * 70}")
        print(f"URL: {page['url']}")
        print(f"Enhanced: {page.get('enhanced', False)}")
        
        if page.get('enhanced'):
            print(f"\n📌 Business Context: {page.get('business_context', 'N/A')}")
            print(f"📌 Content Type: {page.get('content_type', 'N/A')}")
            print(f"📌 Key Information: {', '.join(page.get('key_information', []))}")
            print(f"\n📄 Enhanced Content:")
            print("-" * 70)
            content = str(page.get('main_content', 'N/A'))
            print(content[:500])
            if len(content) > 500:
                print("... (truncated)")
        else:
            print("\n⚠️  Enhancement failed, using original content")
    
    print()
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    
    # Save results
    output_file = 'test_enhancement_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show comparison
    print("\n📊 BEFORE vs AFTER COMPARISON")
    print("-" * 70)
    original_length = sum(len(p['main_content']) for p in SAMPLE_DATA)
    enhanced_length = sum(len(p.get('main_content', '')) for p in enhanced_data)
    
    print(f"Original total length: {original_length} chars")
    print(f"Enhanced total length: {enhanced_length} chars")
    print(f"Difference: {enhanced_length - original_length:+d} chars ({((enhanced_length/original_length - 1) * 100):+.1f}%)")
    
    success_count = sum(1 for p in enhanced_data if p.get('enhanced'))
    print(f"\nSuccessfully enhanced: {success_count}/{len(SAMPLE_DATA)} pages")
    print(f"Success rate: {(success_count/len(SAMPLE_DATA)*100):.1f}%")


async def test_selective_enhancement():
    """Test selective enhancement (only enhance pages that need it)."""
    
    print("\n\n")
    print("=" * 70)
    print("🔍 SELECTIVE ENHANCEMENT TEST")
    print("=" * 70)
    print()
    
    enhancer = ContentEnhancer()
    
    for i, page in enumerate(SAMPLE_DATA, 1):
        needs_it = enhancer.needs_enhancement(page)
        print(f"Page {i}: {page['title']}")
        print(f"  Needs enhancement: {'✅ Yes' if needs_it else '❌ No'}")
        print(f"  Content length: {len(page['main_content'])} chars")
        print(f"  'Learn More' count: {page['main_content'].count('Learn More')}")
        print()


if __name__ == "__main__":
    print("\n🚀 Starting AI Content Enhancement Tests\n")
    
    # Run tests
    asyncio.run(test_enhancement())
    asyncio.run(test_selective_enhancement())
    
    print("\n✅ All tests complete!")
    print("\n💡 Tip: Check 'test_enhancement_results.json' to see the detailed results")

