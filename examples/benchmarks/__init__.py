"""
SlimZero Benchmark Suite

Demonstrates token savings, semantic preservation, and performance across
different prompt types and sizes.
"""

import time
import statistics
from dataclasses import dataclass
from typing import List, Optional

from slimzero import SlimZero
from slimzero.schemas import SlimZeroResult
from slimzero.utils import count_tokens


@dataclass
class BenchmarkCase:
    name: str
    prompt: str
    system_prompt: Optional[str] = None
    history: Optional[List[dict]] = None
    few_shot_examples: Optional[List[str]] = None


@dataclass
class BenchmarkResult:
    case_name: str
    original_tokens: int
    compressed_tokens: int
    token_savings: int
    savings_percent: float
    latency_ms: float
    stages_applied: List[str]


class SlimZeroBenchmark:
    def __init__(self, model: str = "mock", token_budget: int = 4096):
        self.model = model
        self.token_budget = token_budget
        self.sz = SlimZero(model=model, token_budget=token_budget)

    def run_case(self, case: BenchmarkCase) -> BenchmarkResult:
        start = time.perf_counter()
        result = self.sz.call(
            prompt=case.prompt,
            system_prompt=case.system_prompt,
            history=case.history,
            few_shot_examples=case.few_shot_examples,
        )
        latency = (time.perf_counter() - start) * 1000

        return BenchmarkResult(
            case_name=case.name,
            original_tokens=result.original_input_tokens,
            compressed_tokens=result.sent_input_tokens,
            token_savings=result.input_token_savings,
            savings_percent=result.input_token_savings_percent,
            latency_ms=latency,
            stages_applied=result.stages_applied,
        )

    def run_suite(self, cases: List[BenchmarkCase]) -> List[BenchmarkResult]:
        return [self.run_case(case) for case in cases]

    def print_report(self, results: List[BenchmarkResult]) -> None:
        print("\n" + "=" * 80)
        print("SlimZero Benchmark Report")
        print("=" * 80)
        print(f"{'Case':<30} {'Original':>10} {'Compressed':>10} {'Savings':>10} {'Latency':>10}")
        print("-" * 80)

        total_original = 0
        total_compressed = 0

        for r in results:
            print(
                f"{r.case_name:<30} "
                f"{r.original_tokens:>10} "
                f"{r.compressed_tokens:>10} "
                f"{r.savings_percent:>9.1f}% "
                f"{r.latency_ms:>9.1f}ms"
            )
            total_original += r.original_tokens
            total_compressed += r.compressed_tokens

        print("-" * 80)
        overall_savings = ((total_original - total_compressed) / total_original * 100) if total_original > 0 else 0
        print(
            f"{'TOTAL/AVERAGE':<30} "
            f"{total_original:>10} "
            f"{total_compressed:>10} "
            f"{overall_savings:>9.1f}% "
            f"{statistics.mean(r.latency_ms for r in results):>9.1f}ms"
        )
        print("=" * 80)

        print("\nStages Applied:")
        for r in results:
            stages_str = ", ".join(r.stages_applied)
            print(f"  {r.case_name}: {stages_str}")


def get_standard_benchmark_cases() -> List[BenchmarkCase]:
    return [
        BenchmarkCase(
            name="Short Query",
            prompt="What is Python?",
        ),
        BenchmarkCase(
            name="Medium Request",
            prompt="Explain how to implement a binary search tree in Python with example code and time complexity analysis.",
        ),
        BenchmarkCase(
            name="Long Technical",
            prompt="""I need to build a REST API using Flask that handles user authentication with JWT tokens, 
            database connections to PostgreSQL, and implements CRUD operations for a blog post system. 
            Please include error handling, input validation, and middleware for request logging.
            The API should support pagination, filtering, and sorting for the blog posts endpoint.
            Include examples of how to write unit tests using pytest.
            Also add documentation using OpenAPI/Swagger specification.""",
        ),
        BenchmarkCase(
            name="Code Review",
            prompt="""Please review this Python code for a microservice that handles order processing:
            
            class OrderProcessor:
                def __init__(self, db_connection):
                    self.db = db_connection
                    
                def process_order(self, order_id):
                    order = self.db.get_order(order_id)
                    if not order:
                        return {"error": "Order not found"}
                    
                    items = self.db.get_order_items(order_id)
                    total = sum(item.price * item.quantity for item in items)
                    
                    if total > 1000:
                        order.status = "pending_approval"
                    else:
                        order.status = "confirmed"
                        self._process_payment(order, total)
                    
                    self.db.save_order(order)
                    return {"status": order.status}
                    
                def _process_payment(self, order, amount):
                    # TODO: implement payment processing
                    pass
            
            Provide feedback on: error handling, security, performance, and best practices.""",
        ),
        BenchmarkCase(
            name="Conversational",
            prompt="I was trying to set up a CI/CD pipeline with GitHub Actions for my Django project. I followed the tutorial but my tests are failing with database connection errors. Here's my workflow file: name: CI on: push jobs: test runs-on: ubuntu-latest services: postgres image: postgres:14 environment: POSTGRES_DB: test_db steps: - uses: actions/checkout@v3 - name: Set up Python uses: actions/setup-python@v4 with: python-version: '3.11' - run: pip install -r requirements.txt - run: pytest",
            history=[
                {"role": "user", "content": "I need help with GitHub Actions"},
                {"role": "assistant", "content": "I'd be happy to help! What specific issue are you encountering?"},
                {"role": "user", "content": "My tests fail with database connection errors"},
                {"role": "assistant", "content": "That usually means the PostgreSQL service isn't ready when tests run. Add 'needs: postgres' to your test job."},
            ],
        ),
        BenchmarkCase(
            name="Few-Shot Learning",
            prompt='Convert this JSON to YAML: {"name": "John", "age": 30, "city": "New York"}',
            few_shot_examples=[
                'JSON: {"key": "value"} -> YAML: key: value',
                'JSON: {"nested": {"inner": "data"}} -> YAML: nested:\\n  inner: data',
            ],
        ),
    ]


def run_benchmarks() -> List[BenchmarkResult]:
    benchmark = SlimZeroBenchmark()
    cases = get_standard_benchmark_cases()
    results = benchmark.run_suite(cases)
    benchmark.print_report(results)
    return results


if __name__ == "__main__":
    print("Running SlimZero Benchmark Suite...")
    run_benchmarks()
