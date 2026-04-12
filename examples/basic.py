"""
SlimZero Integration Examples

Three-line drop-in integration with OpenAI/Anthropic clients.
"""

from slimzero import SlimZero

__all__ = ["examples"]


def example_openai():
    """Example with OpenAI client."""
    try:
        from openai import OpenAI

        client = OpenAI()

        sz = SlimZero(
            model="gpt-4o",
            api_client=client,
            token_budget=512,
        )

        result = sz.call(prompt="Explain gradient descent please")
        print(f"Response: {result.response}")
        print(f"Tokens saved: {result.input_token_savings_percent:.1f}%")
    except ImportError:
        print("OpenAI client not installed. Run: pip install openai")


def example_anthropic():
    """Example with Anthropic client."""
    try:
        from anthropic import Anthropic

        client = Anthropic()

        sz = SlimZero(
            model="claude-sonnet-4-6",
            api_client=client,
            token_budget=1024,
        )

        result = sz.call(
            prompt="Write a function to calculate fibonacci numbers",
            system_prompt="You are a helpful coding assistant.",
        )
        print(f"Response: {result.response}")
        print(f"Stages: {result.stages_applied}")
    except ImportError:
        print("Anthropic client not installed. Run: pip install anthropic")


def example_bare():
    """Example without API client (mock response)."""
    sz = SlimZero(model="mock")

    result = sz.call(
        prompt="Please could you explain how Python decorators work?",
        few_shot_examples=[
            "Q: What is a closure?\nA: A closure is a function that captures variables from its enclosing scope.",
        ],
    )

    print(f"Original: {result.original_prompt}")
    print(f"Compressed: {result.sent_prompt}")
    print(f"Savings: {result.input_token_savings_percent:.1f}%")


if __name__ == "__main__":
    print("=" * 50)
    print("Example 1: Bare (mock response)")
    print("=" * 50)
    example_bare()

    print("\n" + "=" * 50)
    print("SlimZero integration complete!")
    print("=" * 50)
