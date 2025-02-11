import asyncio
from datetime import datetime, timedelta
from random import random
from typing import Optional, Union, Dict, Any

from quancri.models.tool_model import ToolCategory
from quancri.tools.tool import Tool
import yfinance as yf

class StockPriceTool(Tool):
    """A tool for fetching and analyzing stock price data only. It should only be used when user requires data about real-time stock data.

    This tool provides:
    1. Real-time stock prices
    2. Historical price data for specific dates for a given stock ticker
    3. Historical price data for date ranges for a given stock ticker
    4. Aggregated price statistics (e.g., averages)

    Date inputs can be specified as:
    - Exact dates (YYYY-MM-DD)
    - Relative dates ('past X days')
    - Common periods ('last week', 'past month')
    """

    name = "Stock Price Tool"
    description = "Fetches and analyzes stock market data with support for historical periods and aggregations. It should only be used when user requires data about real-time stock data."
    category = ToolCategory.FINANCE

    async def execute(self,
                      symbol: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      date: Optional[str] = None,
                      period: Optional[str] = None,
                      calculate_average: bool = False,
                      previous_result: Optional[Dict[str, Any]] = None) -> Union[float, Dict[str, float], Dict[str, Any]]:
        """Fetch and analyze stock price data.

        Args:
        symbol: Stock ticker symbol (e.g., 'AAPL' for Apple Inc.)
        start_date: Start date for historical data (YYYY-MM-DD)
        end_date: End date for historical data (YYYY-MM-DD)
        date: Specific date for single day price (YYYY-MM-DD)
        period: Time period for historical data ('7d' for 7 days, '1m' for 1 month)
        calculate_average: Whether to include average price in the response
        previous_result: Optional result from a previous step containing stock data.
                           Can be used to perform calculations on previously fetched data
                           without making new API calls.
        
        Returns:
        Union[float, Dict[str, float], Dict[str, Any]]:
        - Single price value for current/specific date
        - Dictionary of dates->prices for historical data
        - Dictionary with prices and statistics when calculate_average=True

        Examples:
            # Get current price
            >>> await execute(symbol="AAPL")
            150.25

            # Get past average for past 7 days
            >>> await execute(symbol="AAPL", period="7d", calculate_average=True)
            {
                "prices": {
                    "2025-01-25": 150.25,
                    ...
                },
                "average": 151.75,
                "period": "7 days"
            }
            
        """
        def parse_relative_date(date_str: str) -> datetime:
            if not date_str or date_str.lower() == 'today':
                return datetime.now()
            
            if 'days ago' in date_str.lower():
                try:
                    days = int(date_str.lower().replace('days ago', '').strip())
                    return datetime.now() - timedelta(days=days)
                except ValueError:
                    pass
            
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format. Use 'YYYY-MM-DD', 'today', or 'X days ago'. Got: {date_str}")

        # If we have previous results and they contain price data, use them instead of fetching new data
        if previous_result:
            if isinstance(previous_result, dict):
                # Handle single price result from previous step
                if isinstance(previous_result, (int, float)):
                    return previous_result
                
                # Handle dictionary of prices from previous step
                prices = previous_result.get("prices", previous_result)
                if not isinstance(prices, dict):
                    return previous_result
                
                # If only calculating average from previous prices
                if calculate_average:
                    avg_price = round(sum(prices.values()) / len(prices), 2)
                    return {
                        "prices": prices,
                        "average": avg_price,
                        "period": previous_result.get("period", f"{len(prices)} days")
                    }
                
                # If we need to filter the previous results by date range
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        
                        filtered_prices = {
                            date_str: price 
                            for date_str, price in prices.items()
                            if start_dt <= datetime.strptime(date_str, "%Y-%m-%d") <= end_dt
                        }
                        
                        if calculate_average and filtered_prices:
                            return {
                                "prices": filtered_prices,
                                "average": round(sum(filtered_prices.values()) / len(filtered_prices), 2),
                                "period": f"{(end_dt - start_dt).days + 1} days"
                            }
                        return filtered_prices if filtered_prices else None
                    except (ValueError, TypeError):
                        # If date parsing fails, fall through to normal processing
                        pass

        # If no previous results or they couldn't be used, proceed with original logic
        ticker = yf.Ticker(symbol)
        # Get current stock information
        info = ticker.info

        today_data = ticker.history(period='1d', interval='1m')
        # Get today's data of stock for most recent close price
        current_price = today_data['Close'].iloc[-1] if not today_data.empty else 0.0

        # Convert relative dates to actual dates
        if start_date:
            start_date = parse_relative_date(start_date).strftime("%Y-%m-%d")
        if end_date:
            end_date = parse_relative_date(end_date).strftime("%Y-%m-%d")

        # Calculate date range if period is specified
        if period:

            end_date = datetime.now().strftime("%Y-%m-%d")
            days = int(period[:-1]) if period.endswith('d') else 30  # default to 30 days for other periods
            buffer_days = int(days * 1.5) + 1  # Add 50% buffer for weekends and holidays
            start = datetime.now() - timedelta(days=buffer_days)
            start_date = start.strftime("%Y-%m-%d")

        # Generate price data
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

            historical_data = ticker.history(start=start_date, end=end_date)
            days = (end_date - start_date).days + 1  # Calculate number of days in range

            prices = {}
            # Get all available trading days in the range
            for date, row in historical_data.iterrows():
                date_obj = date.date()
                prices[date_obj.strftime("%Y-%m-%d")] = round(row['Close'], 2)

            if calculate_average and prices:
                avg_price = round(sum(prices.values()) / len(prices), 2)
                return {
                    "prices": prices,
                    "average": avg_price,
                    "period": f"{days} days"
                }
            return prices

        # elif date:
        #
        #     # Return mock price for specific date
        #     return 150.25 + (hash(date) % 5)

        else:
            return current_price