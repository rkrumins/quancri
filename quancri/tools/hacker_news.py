from enum import Enum
from typing import Any, List, Dict

import httpx

from quancri.models.tool_model import ToolCategory
from quancri.tools.tool import Tool

class StoryCategories(Enum):
    POPULAR = "popularity"
    NEW = "newest"
    COMMENT = "most_commented"
    BEST = "best"

class HackerNewsTools(Tool):
    """A tool for fetching and analyzing Hacker News stories, which are only about technology.

    This tool provides:
    - Fetch stories by different sorting criteria. Possible sort_by values are: (popular, newest, best, most_commented)
    - Get configurable number of stories (1-25)
    - Optional story summarization
    
    IMPORTANT: This tool only works with the following sort options:
    - POPULAR (default): "popularity" - Most upvoted tech stories
    - NEW: "newest" - Latest tech stories
    - BEST: "best" - Highest rated tech stories
    - COMMENT: "most_commented" - Most discussed tech stories
    """

    name = "HackerNews Tool"
    description = "Fetches and analyzes technology news from Hacker News with various sorting options"
    category = ToolCategory.NEWS

    async def execute(self,
                     number_of_stories: int = 10,
                     summary_enabled: bool = False,
                     sort_by: str = "popularity"
                     ) -> List[Dict]:
        """Fetch and analyze Hacker News stories based on specified criteria.

        Args:
        number_of_stories: Number of stories to fetch (range: 1-25)
        summary_enabled: Enable story summarization
        sort_by: This is the key parameter that returns stories based on the user question. The value MUST be one of following str values (popular, newest, best, most_commented)

        Returns:
        List[Dict[str, Any]]: List of stories with structure:
            {
                "title": str,
                "url": str,
                "votes": int
            }

        Example:
        >>> await tool.execute(number_of_stories=5, sort_by="newest")
        """

        default_number_of_stories = 10
        if not number_of_stories:
            number_of_stories = default_number_of_stories

        default_fallback_api_url = "https://hacker-news.firebaseio.com/v0/topstories.json"

        if sort_by.strip().lower() == "popularity":
            api_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        elif sort_by.strip().lower() == "newest":
            api_url = "https://hacker-news.firebaseio.com/v0/newstories.json"
        elif sort_by.strip().lower() == "best":
            api_url = "https://hacker-news.firebaseio.com/v0/beststories.json"
        elif sort_by.strip().lower() == "asked":
            api_url = "https://hacker-news.firebaseio.com/v0/askstories.json"
        else:
            print("ERROR: Invalid value specified, taking default by popularity")
            api_url = default_fallback_api_url

        response = httpx.get(api_url)
        story_ids = response.json()
        story_details = []

        for story_id in story_ids[:number_of_stories]:
            story_response = httpx.get("https://hacker-news.firebaseio.com/v0/item/{0}.json".format(story_id))
            story = story_response.json()
            story_title = story["title"]
            story_url = story["url"] if "url" in story else None
            story_votes = story["score"]
            story_details.append({
                "title": story_title,
                "url": story_url,
                "votes": story_votes
            })

        if summary_enabled:
            pass

        return story_details