"""
SlimZero CLI Entry Point

Usage:
    python -m slimzero "Your prompt here"
    slimzero "Your prompt here"
"""

import argparse
import sys

from slimzero import SlimZero


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SlimZero - Zero-overhead prompt compression",
        prog="slimzero",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="The prompt to process",
    )
    parser.add_argument(
        "-m", "--model",
        default="mock",
        help="Model to use (default: mock)",
    )
    parser.add_argument(
        "-t", "--token-budget",
        type=int,
        default=512,
        help="Token budget (default: 512)",
    )
    parser.add_argument(
        "-s", "--system",
        default=None,
        help="System prompt",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show savings statistics",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--export-json",
        metavar="FILE",
        help="Export stats to JSON file",
    )
    parser.add_argument(
        "--export-md",
        metavar="FILE",
        help="Export stats to Markdown file",
    )

    args = parser.parse_args()

    if args.prompt is None:
        parser.print_help()
        print("\nExample: slimzero 'Explain Python decorators please'")
        sys.exit(1)

    try:
        sz = SlimZero(
            model=args.model,
            token_budget=args.token_budget,
        )

        result = sz.call(
            prompt=args.prompt,
            system_prompt=args.system,
        )

        if args.json:
            import json
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("=" * 60)
            print("RESPONSE:")
            print("=" * 60)
            print(result.response)
            print()
            print("=" * 60)
            print("STATS:")
            print("=" * 60)
            print(f"Original tokens: {result.original_input_tokens}")
            print(f"Sent tokens:     {result.sent_input_tokens}")
            print(f"Savings:        {result.input_token_savings_percent:.1f}%")
            print(f"Stages:         {', '.join(result.stages_applied)}")

            if args.stats:
                stats = sz.get_stats()
                print()
                print("=" * 60)
                print("CUMULATIVE STATS:")
                print("=" * 60)
                print(f"Total calls:       {stats['total_calls']}")
                print(f"Tokens saved:       {stats['cumulative_tokens_saved']}")
                print(f"Cost saved:         ${stats['cumulative_estimated_cost_usd']:.6f}")
                print(f"Avg tokens/call:    {stats['avg_tokens_saved_per_call']:.1f}")

        if args.export_json:
            sz.export_stats_json(args.export_json)
            print(f"\nExported JSON to: {args.export_json}")

        if args.export_md:
            sz.export_stats_markdown(args.export_md)
            print(f"\nExported Markdown to: {args.export_md}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
