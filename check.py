import asyncio
import json
from pprint import pprint
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    JsonCssExtractionStrategy,
    LLMConfig,
)


async def getSchema():
    browserConfig = BrowserConfig(headless=False, extra_args=["--disable-web-security"])
    async with AsyncWebCrawler(config=browserConfig) as crawler:
        result = await crawler.arun(
            url="https://www.swiggy.com/city/bangalore/mcdonalds-mantri-square-mall-malleshwaram-rest63317",
            config=CrawlerRunConfig(
                wait_for="css:#browse-menu-btn",
                scan_full_page=True,
                scroll_delay=0.7,
            ),
        )
        schema = JsonCssExtractionStrategy.generate_schema(
            result.html,
            llm_config=LLMConfig(
                provider="gemini/gemini-2.0-flash", api_token="env:GEMINI_API_KEY"
            ),
            target_json_example={
                "name": "McDonald's",
                "outlet": "Malleshwaram",
                "delivery_time": "30-40 mins",
                "menu": [
                    {
                        "name": "Chicken Surprise Burger",
                        "price": 76,
                        "rating": 3.3,
                        "rating_count": 3,
                        "coupon": "Buy 1 Get 1",
                        "description": "Introducing the new Chicken Surprise Burger which has the perfect balance of a crispy fried chicken patty, the crunch of onions and the richness of creamy sauce.",
                        "image": "https://media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_300,h_300,c_fit/FOOD_CATALOG/IMAGES/CMS/2024/6/22/0fbf18a1-5191-4cda-a09d-521a24c8c6ca_25cf57c6-48cc-47bd-b422-17e86b816422.png",
                    },
                    {
                        "name": "Chicken Surprise Burger Combo",
                        "price": 238,
                        "rating": 3.3,
                        "rating_count": 6,
                        "coupon": "Buy 1 Get 1",
                        "description": "Introducing the new Chicken Surprise Burger which has the perfect balance of a crispy fried chicken patty, the crunch of onions and the richness of creamy sauce.",
                        "image": "https://media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_300,h_300,c_fit/FOOD_CATALOG/IMAGES/CMS/2024/6/22/0fbf18a1-5191-4cda-a09d-521a24c8c6ca_25cf57c6-48cc-47bd-b422-17e86b816422.png",
                    },
                ],
            },
        )
        return schema


async def main(schema):
    browserConfig = BrowserConfig(headless=False, extra_args=["--disable-web-security"])
    config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema=schema),
        wait_for="css:#browse-menu-btn",
        scan_full_page=True,
        scroll_delay=0.7,
    )
    async with AsyncWebCrawler(config=browserConfig) as crawler:
        result = await crawler.arun(
            url="https://www.swiggy.com/city/bangalore/mcdonalds-mantri-square-mall-malleshwaram-rest63317",
            config=config,
        )
        menu = json.loads(result.extracted_content)
        pprint(menu)


async def test_crawl():
    # Use this one time
    # schema = await getSchema()
    # pprint(schema)
    schema = {
        "baseFields": [],
        "baseSelector": "div[data-testid='normal-dish-item']",
        "fields": [
            {
                "name": "name",
                "selector": "div[aria-hidden='true'][class*='eqSzsP']",
                "type": "text",
            },
            {
                "name": "price",
                "selector": "div[aria-hidden='true'][class*='gxxfeE'] .sc-aXZVg.chixpw",
                "type": "text",
            },
            {
                "name": "rating",
                "selector": "div[class*='kiDiiu'] .sc-aXZVg.knBukL",
                "type": "text",
            },
            {
                "name": "rating_count",
                "selector": "div[class*='kiDiiu'] .sc-aXZVg.cDIVgt",
                "transform": "strip",
                "type": "text",
            },
            {"name": "coupon", "selector": "div[class*='irlXtI']", "type": "text"},
            {
                "name": "description",
                "selector": "div[aria-hidden='true'][class*='gCijQr']",
                "type": "text",
            },
            {
                "attribute": "src",
                "name": "image",
                "selector": "button[aria-label*='See more information'] img",
                "type": "attribute",
            },
        ],
        "name": "Swiggy Restaurant Menu",
    }
    await main(schema)


if __name__ == "__main__":
    asyncio.run(test_crawl())
