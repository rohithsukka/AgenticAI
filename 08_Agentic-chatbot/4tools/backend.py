from __future__ import annotations

import json
import math
import os
import sqlite3
from typing import Any, Annotated, TypedDict

import requests
from dotenv import load_dotenv

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
    HumanMessage
)
from langchain_core.tools import tool

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


###########################################################################
# Load Environment Variables
###########################################################################

load_dotenv()

REQUIRED_ENV_VARS = [
    "GROQ_API_KEY",
    "TAVILY_API_KEY",
    "OPENWEATHER_API_KEY",
    "ALPHAVANTAGE_API_KEY",
]

missing = [x for x in REQUIRED_ENV_VARS if not os.getenv(x)]

if missing:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing)}"
    )


###########################################################################
# LLM
###########################################################################

llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    reasoning_effort="none",
)


###########################################################################
# Search Tool
###########################################################################

search_tool = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="advanced",
)


###########################################################################
# Calculator Tool
###########################################################################

@tool
def calculator(expression: str) -> str:
    """
    Perform mathematical calculations.

    Examples:
    2+2
    math.sqrt(16)
    15*24
    """

    try:

        allowed = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
        }

        result = eval(
            expression,
            {"__builtins__": {}},
            allowed,
        )

        return str(result)

    except Exception as e:
        return f"Calculation error: {e}"


###########################################################################
# Stock Tool
###########################################################################

@tool
def get_stock_price(symbol: str) -> str:
    """
    Get the latest stock price.

    Example:
    AAPL
    TSLA
    MSFT
    """

    api_key = os.getenv("ALPHAVANTAGE_API_KEY")

    url = (
        "https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE"
        f"&symbol={symbol}"
        f"&apikey={api_key}"
    )

    try:

        response = requests.get(
            url,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if "Global Quote" not in data:
            return json.dumps(data, indent=2)

        quote = data["Global Quote"]

        result = {
            "Symbol": quote.get("01. symbol"),
            "Price": quote.get("05. price"),
            "Open": quote.get("02. open"),
            "High": quote.get("03. high"),
            "Low": quote.get("04. low"),
            "Volume": quote.get("06. volume"),
            "Latest Trading Day": quote.get("07. latest trading day"),
            "Previous Close": quote.get("08. previous close"),
            "Change": quote.get("09. change"),
            "Change Percent": quote.get("10. change percent"),
        }

        return json.dumps(result, indent=2)

    except requests.Timeout:
        return "Stock API request timed out."

    except requests.RequestException as e:
        return f"Stock API error: {e}"

    except Exception as e:
        return str(e)


###########################################################################
# Weather Tool
###########################################################################

@tool
def get_current_weather(location: str) -> str:
    """
    Get current weather.

    Example:

    Hyderabad
    London
    New York
    """

    api_key = os.getenv("OPENWEATHER_API_KEY")

    try:

        geo_response = requests.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={
                "q": location,
                "limit": 1,
                "appid": api_key,
            },
            timeout=10,
        )

        geo_response.raise_for_status()

        places: list[dict[str, Any]] = geo_response.json()

        if not places:
            return f"Location '{location}' not found."

        lat = places[0]["lat"]
        lon = places[0]["lon"]

        city = places[0].get("name", "")
        state = places[0].get("state", "")
        country = places[0].get("country", "")

        weather_response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
            },
            timeout=10,
        )

        weather_response.raise_for_status()

        weather = weather_response.json()

        visibility = weather.get("visibility")

        if visibility:
            visibility = round(visibility / 1000, 1)
        else:
            visibility = "N/A"

        return (
            f"Current weather in {city}, {state}, {country}\n\n"
            f"Condition : {weather['weather'][0]['description'].title()}\n"
            f"Temperature : {weather['main']['temp']} °C\n"
            f"Feels Like : {weather['main']['feels_like']} °C\n"
            f"Humidity : {weather['main']['humidity']}%\n"
            f"Pressure : {weather['main']['pressure']} hPa\n"
            f"Wind Speed : {weather['wind']['speed']} m/s\n"
            f"Visibility : {visibility} km"
        )

    except requests.Timeout:
        return "Weather API timed out."

    except requests.HTTPError as e:

        if e.response.status_code == 401:
            return "Invalid OpenWeather API Key."

        return f"HTTP Error : {e.response.status_code}"

    except Exception as e:
        return str(e)


###########################################################################
# Register Tools
###########################################################################

tools = [
    search_tool,
    calculator,
    get_stock_price,
    get_current_weather,
]

llm_with_tools = llm.bind_tools(tools)


###########################################################################
# Graph State
###########################################################################

class ChatState(TypedDict):

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]


###########################################################################
# Assistant Node
###########################################################################

def assistant_node(state: ChatState):

    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


###########################################################################
# Tool Node
###########################################################################

tool_node = ToolNode(tools)

###########################################################################
# SQLite Checkpointer
###########################################################################

connection = sqlite3.connect(
    "chatbot.db",
    check_same_thread=False,
)

checkpoint = SqliteSaver(connection)


###########################################################################
# Build Graph
###########################################################################

graph = StateGraph(ChatState)

graph.add_node("assistant", assistant_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "assistant")

graph.add_conditional_edges(
    "assistant",
    tools_condition,
)

graph.add_edge(
    "tools",
    "assistant",
)

chatbot = graph.compile(
    checkpointer=checkpoint
)


###########################################################################
# Helper : List All Conversation Threads
###########################################################################

def get_all_threads() -> list[str]:
    """
    Returns every saved thread id.
    """

    thread_ids = set()

    for checkpoint_data in checkpoint.list(None):

        config = checkpoint_data.config

        if (
            "configurable" in config
            and "thread_id" in config["configurable"]
        ):
            thread_ids.add(
                config["configurable"]["thread_id"]
            )

    return sorted(thread_ids)


###########################################################################
# Helper : Get Messages For A Thread
###########################################################################

def get_messages(thread_id: str):
    """
    Returns all saved messages.
    """

    state = chatbot.get_state(
        {
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return state.values.get(
        "messages",
        [],
    )


###########################################################################
# Helper : Extract Tool Execution History
###########################################################################

def get_tool_history(thread_id: str):
    """
    Reconstruct tool execution history from
    AIMessage.tool_calls + ToolMessage.
    """

    messages = get_messages(thread_id)

    tool_history = []

    for index, message in enumerate(messages):

        if not isinstance(message, AIMessage):
            continue

        if not message.tool_calls:
            continue

        for tool_call in message.tool_calls:

            tool_data = {
                "tool_name": tool_call["name"],
                "arguments": tool_call["args"],
                "tool_call_id": tool_call["id"],
                "output": None,
            }

            for later in messages[index + 1:]:

                if (
                    isinstance(later, ToolMessage)
                    and later.tool_call_id
                    == tool_call["id"]
                ):

                    tool_data["output"] = later.content
                    break

            tool_history.append(tool_data)

    return tool_history


###########################################################################
# Helper : Pretty Print Tool History
###########################################################################

def print_tool_history(thread_id: str):

    history = get_tool_history(thread_id)

    if not history:

        print("\nNo tool calls found.\n")
        return

    print("\n" + "=" * 80)
    print("TOOL EXECUTION HISTORY")
    print("=" * 80)

    for i, tool in enumerate(history, start=1):

        print(f"\nTool #{i}")

        print("-" * 80)

        print(
            f"Tool Name : {tool['tool_name']}"
        )

        print(
            "\nArguments:"
        )

        print(
            json.dumps(
                tool["arguments"],
                indent=4,
            )
        )

        print("\nOutput:\n")

        print(tool["output"])

        print("-" * 80)


###########################################################################
# Helper : Debug Graph Execution
###########################################################################

def print_graph_updates(
    user_message: str,
    thread_id: str,
):
    """
    Streams every graph update.

    Useful for understanding LangGraph.
    """

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    for update in chatbot.stream(

        {
            "messages": [
                HumanMessage(
                    content=user_message
                )
            ]
        },

        config=config,

        stream_mode="updates",

    ):

        print("\n")

        print("=" * 80)

        print(update)


###########################################################################
# Helper : Chat
###########################################################################

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def chat(user_message: str, thread_id: str):
    """
    Execute one chat turn and return:

    {
        "answer": "...",
        "messages": [...],
        "tool_history": [...]
    }
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    before_state = chatbot.get_state(config)
    before_messages = before_state.values.get("messages", [])

    chatbot.invoke(
        {
            "messages": [
                HumanMessage(content=user_message)
            ]
        },
        config=config,
    )

    after_state = chatbot.get_state(config)
    after_messages = after_state.values.get("messages", [])

    # Only keep newly-added messages
    new_messages = after_messages[len(before_messages):]

    final_answer = ""

    tool_history = []

    pending_tool_calls = {}

    for message in new_messages:

        if isinstance(message, AIMessage):

            # Final assistant answer
            if message.content:
                final_answer = message.content

            # Tool calls
            if message.tool_calls:

                for tool in message.tool_calls:

                    pending_tool_calls[tool["id"]] = {
                        "tool_name": tool["name"],
                        "arguments": tool["args"],
                        "tool_call_id": tool["id"],
                        "output": None,
                    }

        elif isinstance(message, ToolMessage):

            if message.tool_call_id in pending_tool_calls:

                pending_tool_calls[
                    message.tool_call_id
                ]["output"] = message.content

    tool_history = list(pending_tool_calls.values())

    return {
        "answer": final_answer,
        "messages": new_messages,
        "tool_history": tool_history,
    }


from langchain_core.messages import AIMessage, ToolMessage, HumanMessage


def stream_chat(user_message: str, thread_id: str):
    """
    Stream one conversation turn as structured events.

    Yields dictionaries.

    Event Types

    assistant_started
    tool_started
    tool_finished
    assistant_message
    done
    """

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    pending_tools = {}

    yield {
        "type": "assistant_started"
    }

    for update in chatbot.stream(

        {
            "messages": [
                HumanMessage(content=user_message)
            ]
        },

        config=config,

        stream_mode="updates",

    ):

        #
        # Assistant Node
        #
        if "assistant" in update:

            messages = update["assistant"]["messages"]

            for message in messages:

                if not isinstance(message, AIMessage):
                    continue

                #
                # Tool Calls
                #
                if message.tool_calls:

                    for tool in message.tool_calls:

                        pending_tools[tool["id"]] = {
                            "tool_name": tool["name"],
                            "arguments": tool["args"],
                        }

                        yield {
                            "type": "tool_started",
                            "tool_name": tool["name"],
                            "arguments": tool["args"],
                        }

                #
                # Final Answer
                #
                elif message.content:

                    yield {
                        "type": "assistant_message",
                        "content": message.content,
                    }

        #
        # Tool Node
        #
        elif "tools" in update:

            messages = update["tools"]["messages"]

            for message in messages:

                if not isinstance(message, ToolMessage):
                    continue

                tool = pending_tools.get(
                    message.tool_call_id,
                    {},
                )

                yield {

                    "type": "tool_finished",

                    "tool_name": tool.get(
                        "tool_name",
                        message.name,
                    ),

                    "arguments": tool.get(
                        "arguments",
                        {},
                    ),

                    "output": message.content,

                }

    yield {
        "type": "done"
    }

    
###########################################################################
# Demo
###########################################################################

if __name__ == "__main__":

    THREAD_ID = "demo-thread"

    print("=" * 80)
    print("Agentic Chatbot")
    print("=" * 80)

    while True:

        user = input("\nYou : ")

        if user.lower() in {
            "exit",
            "quit",
        }:
            break

        print("\n")

        print("=" * 80)
        print("GRAPH EXECUTION")
        print("=" * 80)

        print_graph_updates(
            user,
            THREAD_ID,
        )

        answer = chat(
            user,
            THREAD_ID,
        )

        print("\nAssistant:\n")

        print(answer)

        print_tool_history(
            THREAD_ID
        )