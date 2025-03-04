import os
import json
import asyncio
from typing import Dict

from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy

async def extract_structured_data_using_json(
            extra_headers: Dict[str, str] = None
    ):
    print(f"\n--- Extracting Structured Data with json ---")

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        proxy_config=None,
        viewport_width=1080,
        viewport_height=600,
        verbose=True,
        use_persistent_context=False,
        user_data_dir=None,
        cookies=None,
        text_mode=False,
        light_mode=False,
        extra_args=None,
    )

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    schema = {
        "baseSelector": "div.card-body",
        "fields": [
            {"name": "name", "selector": "h4.card-title", "type": "text"},
            {"name": "dynasty", "selector": "p.card-subtitle > span:first-child", "type": "text"},
            {"name": "author", "selector": "p.card-subtitle > span:last-child", "type": "text"},
            {"name": "content", "selector": "div.card-content", "type": "text"},
            {"name": "pinyin_url", "selector": "a.card-link", "type": "attribute", "attribute": "href"}
        ]
    }

    # schema_pinyin = {
    #     "baseSelector": "div.card text-center mb-3",
    #     "fields": [
    #         {"name": "name", "selector": "h4.card-title mr-1", "type": "text"},
    #         {"name": "dynasty", "selector": "p.card-subtitle mb-2 text-muted mr-1 > span:first-child", "type": "text"},
    #         {"name": "author", "selector": "p.card-subtitle mb-2 text-muted mr-1 > span:last-child", "type": "text"},
    #         {"name": "content", "selector": "p.mid-compact py-content", "type": "text"},
    #     ]
    # }
    schema_pinyin = {
        "name": "带注音诗句",
        "baseSelector": "div.card-body",
        "fields": [
            {
                "name": "name",
                "selector": "h4.card-title mr-1",
                "type": "list",
                "fields": [
                    {"name": "汉字", "selector": "h4.card-title mr-1", "type": "text"},
                    {"name": "拼音", "selector": "h4.card-title mr-1", "type": "text"},
                ]
            },
            {"name": "拼音", "selector": "rt", "type": "text"}
        ]
    }

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema)
    )

    crawler_config_pinyin = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema_pinyin)
    )

    # Crawling 75 ancient poems that elementary school students must memorize
    await xiao75(browser_config, crawler_config)


async def xiao75(browser_config, crawler_config):
    baseURL="https://www.shicile.com"
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 定义文件路径
        basePath = os.path.join("./data/")
        filePath = basePath + "xiao75.json"
        # 检查文件是否存在
        if os.path.exists(filePath):
            # 如果文件存在，直接读取文件内容
            with open(filePath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("文件已存在，直接读取内容。")
        else:
            result = await crawler.arun(
                url=baseURL + "/plist/kebian2011xiao-s1-e75", config=crawler_config
            )
            data = json.loads(result.extracted_content)

            # 递归爬取每首诗的拼音版本
            for item in data:
                pinyin_url = item["pinyin_url"]
                if pinyin_url:
                    item["pinyin_url"] = baseURL+pinyin_url

            # 检查目录是否存在，如果不存在则创建
            os.makedirs(os.path.dirname(filePath), exist_ok=True)
            with open(filePath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        # 根据data内容再进行处理
        xiao75Path = basePath + "/xiao75"
        index=1
        for item in data:
            # 创建诗的目录
            path = xiao75Path + "/" + str(index) + "." + item["name"]
            os.makedirs(path, exist_ok=True)
            fileName=path + "/" + item["name"] + ".json"
            with open(fileName, "w", encoding="utf-8") as f:
                json.dump(item, f, ensure_ascii=False, indent=4)
            index=index+1

if __name__ == "__main__":
    # Use JsonCssExtractionStrategy
    asyncio.run(
        extract_structured_data_using_json()
    )