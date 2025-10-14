"""
Test script to demonstrate the dynamic prompt generation feature.

This script shows how the system analyzes website content and generates
personalized chatbot system prompts.
"""

from prompt_generator import PromptGenerator
import json

def main():
    print("=" * 80)
    print("Dynamic System Prompt Generator - Test")
    print("=" * 80)
    print()
    
    # Generate prompt from existing scraped data
    print("📊 Analyzing website data from: web_scraping_results.json")
    print()
    
    try:
        # Load and display some website info
        with open('web_scraping_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if data:
            homepage = data[0]
            print(f"🌐 Website URL: {homepage.get('url', 'N/A')}")
            print(f"📄 Homepage Title: {homepage.get('title', 'N/A')}")
            print()
            
            # Extract business info
            business_name = PromptGenerator._extract_business_name(data)
            business_type = PromptGenerator._identify_business_type(data)
            specialization = PromptGenerator._extract_specialization(data, business_type)
            services = PromptGenerator._extract_services_or_offerings(data)
            
            print("🔍 Analysis Results:")
            print("-" * 80)
            print(f"Business Name: {business_name or 'Not detected'}")
            print(f"Business Type: {business_type}")
            print(f"Specialization: {specialization or 'None detected'}")
            print(f"Services Found: {len(services)}")
            if services:
                print("\nKey Services/Offerings:")
                for i, service in enumerate(services[:5], 1):
                    print(f"  {i}. {service}")
            print()
            
            # Generate the prompt
            print("🤖 Generated System Prompt:")
            print("=" * 80)
            prompt = PromptGenerator.generate_system_prompt()
            print(prompt)
            print("=" * 80)
            print()
            
            print("✅ Success! The chatbot will now use this personalized prompt.")
            print("💡 This prompt is automatically generated based on website content.")
            print()
            
            # Show the difference
            print("📝 Comparison:")
            print("-" * 80)
            print("OLD (Generic) Prompt:")
            print("  'You're a helpful assistant. Answer based on the context below.'")
            print()
            print("NEW (Personalized) Prompt:")
            first_line = prompt.split('\n')[0]
            print(f"  '{first_line}...'")
            print()
            print("The new prompt is context-aware and reflects the actual business!")
            
    except FileNotFoundError:
        print("❌ Error: web_scraping_results.json not found")
        print("Please run the scraping first by initializing a website.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

