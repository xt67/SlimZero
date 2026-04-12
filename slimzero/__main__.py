"""
SlimZero CLI Entry Point

Usage:
    python -m slimzero "Your prompt here"
    slimzero "Your prompt here"
"""

import sys


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: slimzero <prompt>")
        print("       python -m slimzero <prompt>")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    print(f"SlimZero CLI - Processing prompt: {prompt[:50]}...")
    print("Note: Full SlimZero functionality requires API credentials and model configuration.")
    print("See README.md for setup instructions.")


if __name__ == "__main__":
    main()
