from smart_agent.agents.agents import Agent
from smart_agent.llm_clients.llm_client import LangChainProvider
from smart_agent.models.llm_model import LLMConfig
from smart_agent.tools.hacker_news import HackerNewsTools
from smart_agent.tools.news_api import NewsAPIClient
from smart_agent.tools.stock_tools import StockPriceTool
from smart_agent.tools.weather_tools import WeatherTool

import os

# Example usage:
async def main():
    try:
        llm_config = LLMConfig(
            api_key="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",
            model="deepseek-r1-distill-llama-70b",
            temperature=0.1
        )
        llm_provider = LangChainProvider(llm_config)
        agent = Agent(llm_provider)
        # Initialize agent with GPT interface

        # # Register tools
        agent.register_tool(StockPriceTool())
        agent.register_tool(NewsAPIClient(api_key="8182bcdf63354d8a8e76b8bef85c12f0"))
        # agent.register_tool(WeatherTool())
        #
        # # Process question
        # question = "What is the current stock price of AAPL?"
        # response = await agent.process_question(question)
        # print(f"Response: {response}")

        # question = "Tell me about the impact of globalisation on the society?"
        # response = await agent.process_question(question)
        # print(f"Response: {response}")
        # # Process question
        # question = "Give me all the stock prices of AAPL and average price for past 10 trading days and then tell me whether they are correlated to the weather in New York? Provide me a detailed report"
        # response = await agent.process_question(question)
        # print(f"Response: {response}")
        #
        # # Process question
        # question = "Provide me insights on Apple stock for past 30 days and produce a detailed analysis whether it is a BUY or SELL? As a part of this analysis, check for any financial news related to Apple that might impact the stock price"
        # response = await agent.process_question(question)
        # print(f"Response: {response}")
        #
        # # Process question
        question = "Provide me insights on Apple stock for past 10 days and produce a detailed analysis whether it is a BUY or SELL based on the weather in Cupertino for each of past 5 days. Determine whether there is a correlation hetween the news and stock price?"
        response = await agent.process_question(question)
        print(f"Response: {response}")
        #
        # weather_agent = Agent(llm_provider)
        # weather_agent.register_tool(WeatherTool())
        # question = "What is the weather like in London today?"
        # response = await weather_agent.process_question(question)
        # print(f"Weather Response: {response}")
        #
        # question = "What is the weather like in the Big Apple today?"
        # response = await weather_agent.process_question(question)
        # print(f"Weather Response: {response}")
        #
        # question = "Is it a good day for a football match outdoors?"
        # response = await weather_agent.process_question(question)
        # print(f"Weather Response: {response}")

        # agent.register_tool(StockPriceTool())
        # agent.register_tool(HackerNewsTools())
        # question = "What are the newest 100 stories in tech on Hacker News and are any of those relates to Apple stock and do those have any impact on the stock price potentially?"
        # response = await agent.process_question(question)
        # print(f"Hacker News Response: {response}")

        # question = "What is the meaning of life"
        # response = await agent.process_question(question)
        # print(f"Response: {response}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio

    # Run the async main function
    asyncio.run(main())
