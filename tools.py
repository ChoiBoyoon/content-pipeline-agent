import os, re

from crewai.tools import BaseTool
from firecrawl import FirecrawlApp, ScrapeOptions
from typing import Type
from pydantic import BaseModel, Field

class WebSearchInput(BaseModel):
    """Input schema for WebSearchTool."""
    query: str = Field(..., description="The search query to look up on the web")

class WebSearchTool(BaseTool):
    name: str = "web_search_tool"
    description: str = "A tool for searching the web and returning results in markdown format"
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        """Execute the web search."""
        app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

        response = app.search(
            query=query,
            limit=5, #temp
            scrape_options=ScrapeOptions(formats=["markdown"])
        )

        if not response.success:
            return "Error using tool."

        cleaned_chunks = []

        for result in response.data:
            title = result["title"]
            url = result["url"]
            markdown = result["markdown"]

            cleaned = re.sub(r"\\+|\n+", "", markdown).strip() #remove unnecessary whitespaces to save tokens
            cleaned = re.sub(r"\[[^\]]+\]\([^\)]+\)|https?://[^\s]+", "", cleaned) #remove urls
            cleaned_result = {
                'title':title,
                'url':url,
                'markdown':cleaned,
            }

            cleaned_chunks.append(cleaned_result)
        return str(cleaned_chunks)

# Create an instance of the tool
web_search_tool = WebSearchTool()