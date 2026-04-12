"""
SlimZero LangChain Integration Example

Shows how to integrate SlimZero with LangChain.
"""

from langchain_openai import OpenAI
from langchain.schema import HumanMessage, SystemMessage
from slimzero import SlimZero


def example_basic():
    """Basic LangChain + SlimZero integration."""
    llm = OpenAI(model="gpt-4o", temperature=0)
    sz = SlimZero(model="gpt-4o", token_budget=512)

    prompt = "Please could you explain to me how neural networks work in detail, with examples if possible?"

    result = sz.call(prompt=prompt)

    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content=result.sent_prompt),
    ]

    response = llm(messages)
    print(f"Response: {response.content}")
    print(f"Tokens saved: {result.input_token_savings_percent:.1f}%")


def example_with_callback():
    """LangChain with SlimZero compression and callbacks."""
    from langchain.callbacks import StdOutCallbackHandler

    llm = OpenAI(model="gpt-4o", temperature=0)
    sz = SlimZero(model="gpt-4o", token_budget=512)

    user_prompt = "Explain the difference between supervised and unsupervised learning, and give some examples of each."

    result = sz.call(prompt=user_prompt)

    handler = StdOutCallbackHandler()
    messages = [HumanMessage(content=result.sent_prompt)]

    response = llm(messages, callbacks=[handler])
    print(f"\nCompressed prompt: {result.sent_prompt[:100]}...")
    print(f"Response: {response.content[:200]}...")


def example_agent():
    """LangChain Agent with SlimZero compression."""
    from langchain.agents import initialize_agent, Tool
    from langchain_openai import OpenAI

    llm = OpenAI(model="gpt-4o", temperature=0)
    sz = SlimZero(model="gpt-4o", token_budget=512)

    def search(query: str) -> str:
        """Mock search function."""
        return f"Results for: {query}"

    tools = [
        Tool(
            name="Search",
            func=search,
            description="Search for information",
        ),
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent="zero-shot-react-description",
        verbose=True,
    )

    user_goal = "I need to understand how to implement a binary search tree in Python, please help me research and explain"

    result = sz.call(prompt=user_goal)

    agent.run(result.sent_prompt)


if __name__ == "__main__":
    print("=" * 60)
    print("Example 1: Basic Integration")
    print("=" * 60)
    example_basic()

    print("\n" + "=" * 60)
    print("Example 2: With Callbacks")
    print("=" * 60)
    example_with_callback()
