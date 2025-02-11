import os
from datetime import timedelta, datetime
from typing import Any, Dict, List, Optional
import requests

from quancri.tools.tool import Tool


import requests
from datetime import datetime, timedelta
import pandas as pd
import json
from typing import List, Dict, Optional, Union
import os
from dotenv import load_dotenv


class NewsAPIClient(Tool):
    """
    A comprehensive client for fetching and managing news articles using the NewsAPI service.

    This class provides multiple methods to fetch news articles based on various criteria
    including keywords, companies, publishers, and sectors. It supports both the 'everything'
    and 'top-headlines' NewsAPI endpoints, multiple output formats (CSV, JSON), and includes
    comprehensive error handling.

    When uysing this, you must only use these supported sectors: technology, finance, healthcare, energy, automotive, retail, media. For banking-related queries, use "finance" as the sector.

    Methods:
        fetch_articles(keyword, days=20, language="en", sort_by="publishedAt"):
            Fetch news articles based on keyword and time range.

            Example:
                >>> client = NewsAPIClient()
                >>> articles = fetch_articles("Bitcoin", days=7)
                >>> print(f"Found {len(articles)} articles about Bitcoin")

        fetch_company_news(company_name, include_ticker=True, days=20, language="en"):
            Fetch news specifically about a company, optionally including stock ticker mentions.

            Example:
                >>> # Get Tesla news including stock ticker (TSLA) mentions
                >>> tesla_news = fetch_company_news("Tesla")
                >>> # Get Apple news without stock ticker
                >>> apple_news = fetch_company_news("Apple", include_ticker=False)

        fetch_from_publisher(publisher, keyword=None, days=20, language="en"):
            Fetch articles from a specific news source, optionally filtered by keyword.

            Example:
                >>> # All recent TechCrunch articles
                >>> tc_news = fetch_from_publisher("techcrunch.com")
                >>> # Reuters articles about climate change
                >>> climate_news = fetch_from_publisher(
                ...     "reuters.com",
                ...     keyword="climate change"
                ... )

        fetch_sector_news(sector, country=None, max_articles=100):
            Fetch popular news articles about a specific sector.
            Supported sectors: technology, finance, healthcare, energy, automotive, retail, media

            Example:
                >>> # Get US technology sector news
                >>> tech_news = fetch_sector_news("technology", country="us")
                >>> # Get global healthcare news
                >>> health_news = fetch_sector_news("healthcare")
                >>> # Get global finance news
                >>> finance_news = fetch_sector_news("finance")

        fetch_trending_headlines(category=None, country="us", max_articles=20):
            Fetch trending headlines, optionally filtered by category and country.
            Supported categories: business, entertainment, general, health,
            science, sports, technology

            Example:
                >>> # Get top US headlines
                >>> headlines = fetch_trending_headlines()
                >>> # Get UK technology headlines
                >>> tech_headlines = fetch_trending_headlines(
                ...     category="technology",
                ...     country="gb"
                ... )

        save_articles(articles, output_format="csv", filename=None):
            Save fetched articles to a file in CSV or JSON format.

            Example:
                >>> articles = fetch_articles("AI")
                >>> # Save as CSV with custom filename
                >>> save_articles(articles, "csv", "ai_news")
                >>> # Save as JSON with auto-generated filename
                >>> save_articles(articles, "json")

    Usage Example:
        >>> # Fetch technology news from multiple sources
        >>> tech_news = fetch_sector_news("technology")
        >>> tech_crunch = fetch_from_publisher("techcrunch.com")
        >>> ai_news = fetch_articles("artificial intelligence")
        >>>
        >>> # Save results in different formats
        >>> save_articles(tech_news, "csv", "tech_sector_news")
        >>> save_articles(tech_crunch, "json", "techcrunch_articles")
        >>> save_articles(ai_news, "csv", "ai_developments")

    Note:
        - API key must be provided either directly or through NEWSAPI_KEY environment variable
        - Some methods have rate limits based on your NewsAPI subscription
        - Articles can be filtered by language, country, and other parameters
        - Default language is English ("en") for most methods
        - CSV and JSON output formats are supported for saving articles
    """

    async def execute(self, **kwargs) -> Any:
        pass

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the NewsAPI client. See class docstring for details."""
        load_dotenv()
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided either directly or through NEWSAPI_KEY environment variable")

        self.base_url_everything = "https://newsapi.org/v2/everything"
        self.base_url_top = "https://newsapi.org/v2/top-headlines"
        self.headers = {"X-Api-Key": self.api_key}
        self.default_page_size = 10  # Set default page size

    def fetch_articles(
            self,
            keyword: str,
            days: int = 20,
            language: str = "en",
            sort_by: str = "relevancy",
            max_articles: int = None
    ) -> List[Dict]:
        """
        Fetch news articles based on keyword and time range.

        Args:
            keyword (str): Search term to query articles for
            days (int): Number of past days to search for. Defaults to 20
            language (str): Article language code. Defaults to "en"
            sort_by (str): Sorting criteria ("publishedAt", "relevancy", "popularity")
            max_articles (int, optional): Maximum number of articles to fetch. Defaults to self.default_page_size

        Returns:
            List[Dict]: List of article dictionaries
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        params = {
            "q": keyword,
            "language": language,
            "sortBy": sort_by,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "pageSize": min(max_articles or self.default_page_size, 10)  # API limit is 100
        }

        return self._make_request(self.base_url_everything, params)

    def fetch_company_news(
            self,
            company_name: str,
            include_ticker: bool = True,
            days: int = 20,
            language: str = "en",
            max_articles: int = None
    ) -> List[Dict]:
        """
        Fetch news articles about a specific company.

        Args:
            company_name (str): Name of the company
            include_ticker (bool): Whether to include stock ticker in search
            days (int): Number of past days to search for
            language (str): Article language code

        Returns:
            List[Dict]: List of article dictionaries

        Examples:
            >>> tesla_news = client.fetch_company_news("Tesla")
            >>> apple_news = client.fetch_company_news("Apple", include_ticker=True)
        """
        # Common stock tickers mapping (expand as needed)
        company_tickers = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX"
        }

        query = company_name
        if include_ticker:
            ticker = company_tickers.get(company_name.lower())
            if ticker:
                query = f"({company_name} OR {ticker})"

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        params = {
            "q": query,
            "language": language,
            "sortBy": "relevancy",
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "pageSize": min(max_articles or self.default_page_size, 100)
        }

        return self._make_request(self.base_url_everything, params)

    def fetch_from_publisher(
            self,
            publisher: str,
            keyword: Optional[str] = None,
            days: int = 20,
            language: str = "en",
            max_articles: int = None
    ) -> List[Dict]:
        """
        Fetch articles from a specific publisher.

        Args:
            publisher (str): Publisher domain (e.g., "techcrunch.com")
            keyword (Optional[str]): Optional keyword to filter articles
            days (int): Number of past days to search for
            language (str): Article language code

        Returns:
            List[Dict]: List of article dictionaries

        Examples:
            >>> # All articles from TechCrunch
            >>> tc_news = fetch_from_publisher("techcrunch.com")
            >>> # Tesla articles from Reuters
            >>> tesla_reuters = fetch_from_publisher("reuters.com", "Tesla")
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        params = {
            "domains": publisher,
            "language": language,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "pageSize": min(max_articles or self.default_page_size, 100)
        }

        if keyword:
            params["q"] = keyword

        return self._make_request(self.base_url_everything, params)

    def fetch_sector_news(
            self,
            sector: str,
            country: Optional[str] = None,
            max_articles: int = None
    ) -> List[Dict]:
        """
        Fetch popular news articles about a specific sector.

        Args:
            sector (str): Sector name (e.g., "technology", "finance")
            country (Optional[str]): Two-letter country code (e.g., "us", "gb")
            max_articles (int): Maximum number of articles to fetch

        Returns:
            List[Dict]: List of article dictionaries

        Examples:
            >>> tech_news = fetch_sector_news("technology")
            >>> uk_finance = fetch_sector_news("finance", country="gb")
        """
        # Sector-specific keywords mapping
        sector_keywords = {
            "technology": "technology OR tech OR software OR AI OR artificial intelligence OR cybersecurity",
            "finance": "finance OR banking OR investment OR stock market OR cryptocurrency",
            "healthcare": "healthcare OR medical OR biotech OR pharma OR medicine",
            "energy": "energy OR oil OR renewable OR solar OR wind power",
            "automotive": "automotive OR cars OR electric vehicles OR EV OR autonomous driving",
            "retail": "retail OR e-commerce OR shopping OR consumer",
            "media": "media OR entertainment OR streaming OR gaming"
        }

        if sector.lower() not in sector_keywords:
            raise ValueError(f"Unsupported sector. Supported sectors: {', '.join(sector_keywords.keys())}")

        params = {
            "q": sector_keywords[sector.lower()],
            "sortBy": "popularity",
            "pageSize": min(max_articles or self.default_page_size, 100)
        }

        if country:
            params["country"] = country.lower()
            return self._make_request(self.base_url_top, params)
        else:
            return self._make_request(self.base_url_everything, params)

    def fetch_trending_headlines(
            self,
            category: Optional[str] = None,
            country: str = "us",
            max_articles: int = None
    ) -> List[Dict]:
        """
        Fetch trending headlines, optionally filtered by category.

        Args:
            category (Optional[str]): News category (business, technology, etc.)
            country (str): Two-letter country code
            max_articles (int): Maximum number of articles to fetch

        Returns:
            List[Dict]: List of article dictionaries

        Examples:
            >>> top_news = fetch_trending_headlines()
            >>> tech_headlines = fetch_trending_headlines("technology")
        """
        params = {
            "country": country.lower(),
            "pageSize": min(max_articles or self.default_page_size, 100)
        }

        if category:
            params["category"] = category.lower()

        return self._make_request(self.base_url_top, params)

    def _make_request(self, url: str, params: Dict) -> List[Dict]:
        """
        Make HTTP request to NewsAPI.

        Args:
            url (str): API endpoint URL
            params (Dict): Query parameters

        Returns:
            List[Dict]: List of article dictionaries
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("articles", [])

        except requests.exceptions.RequestException as e:
            print(f"Error fetching articles: {e}")
            return []

    def save_articles(
            self,
            articles: List[Dict],
            output_format: str = "csv",
            filename: Optional[str] = None
    ) -> None:
        """
        Save articles to file. See previous docstring for details.
        """
        if not articles:
            print("No articles to save")
            return

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_articles_{timestamp}"

        try:
            if output_format.lower() == "csv":
                df = pd.DataFrame(articles)
                df.to_csv(f"{filename}.csv", index=False)
                print(f"Articles saved to {filename}.csv")

            elif output_format.lower() == "json":
                with open(f"{filename}.json", "w", encoding="utf-8") as f:
                    json.dump(articles, f, indent=2, ensure_ascii=False)
                print(f"Articles saved to {filename}.json")

            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        except Exception as e:
            print(f"Error saving articles: {e}")
