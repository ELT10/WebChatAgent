import asyncio
from scraping_agents import WebScrapingAgent, VisualScrapingAgent
import json

async def test_scraping():
    # # Test web scraping
    # web_scraper = WebScrapingAgent("https://sreesuryaayurveda.com")  # Replace with your target website
    # web_data = await web_scraper.scrape_site()
    
    # # Save results
    # with open("web_scraping_results.json", "w", encoding="utf-8") as f:
    #     json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    # Test visual scraping with error handling
    visual_scraper = VisualScrapingAgent("https://sreesuryaayurveda.com")
    try:
        visual_data = await visual_scraper.scrape_site()
    
        # Save results only if successful
        with open("visual_scraping_results.json", "w", encoding="utf-8") as f:
            json.dump(visual_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Visual scraping failed: {str(e)}")
    finally:
        await visual_scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_scraping()) 