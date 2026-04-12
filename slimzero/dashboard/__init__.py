"""
SlimZero Live Dashboard

Rich-based terminal dashboard for real-time savings visualization.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

RICH_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    RICH_AVAILABLE = True
except ImportError:
    logger.warning("Rich not available. Dashboard will be disabled.")


class SlimZeroDashboard:
    """
    Live terminal dashboard showing SlimZero savings in real-time.

    Displays:
    - Cumulative tokens saved
    - Cost savings (USD)
    - Per-call statistics
    - Active stages
    - Hallucination flags
    """

    def __init__(self, console: Optional["Console"] = None):
        """
        Initialize dashboard.

        Args:
            console: Optional Rich Console instance.
        """
        if not RICH_AVAILABLE:
            self._enabled = False
            return

        self._enabled = True
        self._console = console or Console()
        self._live: Optional[Live] = None
        self._stats: Dict[str, Any] = {
            "total_calls": 0,
            "cumulative_tokens_saved": 0,
            "cumulative_cost_saved": 0.0,
            "avg_tokens_saved_per_call": 0.0,
            "input_token_savings_percent": 0.0,
            "hallucination_flags": 0,
            "last_call_time": None,
        }

    @property
    def is_enabled(self) -> bool:
        """Check if dashboard is enabled."""
        return self._enabled

    def start(self) -> None:
        """Start the live dashboard."""
        if not self._enabled or not RICH_AVAILABLE:
            return

        layout = self._create_layout()
        self._live = Live(layout, console=self._console, refresh_per_second=1)
        self._live.start()

    def stop(self) -> None:
        """Stop the live dashboard."""
        if self._live:
            self._live.stop()
            self._live = None

    def _create_layout(self) -> "Layout":
        """Create the dashboard layout."""
        if not RICH_AVAILABLE:
            from rich.layout import Layout as L
            return L()

        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["header"].update(self._create_header())
        layout["main"].update(self._create_main_panel())
        layout["footer"].update(self._create_footer())

        return layout

    def _create_header(self) -> "Panel":
        """Create header panel."""
        if not RICH_AVAILABLE:
            return Panel("SlimZero Dashboard")

        from rich.align import Align
        title = Text("SlimZero", style="bold cyan")
        subtitle = Text("Zero-overhead Prompt Compression", style="dim")
        return Panel(
            Align.center(Text.assemble(title, "\n", subtitle)),
            style="cyan",
        )

    def _create_main_panel(self) -> "Panel":
        """Create main statistics panel."""
        if not RICH_AVAILABLE:
            return Panel("Dashboard content")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="green", width=20)

        table.add_row("Total Calls", str(self._stats["total_calls"]))
        table.add_row(
            "Tokens Saved",
            f"{self._stats['cumulative_tokens_saved']:,}",
        )
        table.add_row(
            "Cost Saved",
            f"${self._stats['cumulative_cost_saved']:.6f}",
        )
        table.add_row(
            "Avg Tokens/Call",
            f"{self._stats['avg_tokens_saved_per_call']:.1f}",
        )
        table.add_row(
            "Savings %",
            f"{self._stats['input_token_savings_percent']:.1f}%",
        )
        table.add_row(
            "Hallucination Flags",
            str(self._stats["hallucination_flags"]),
        )

        return Panel(table, title="[bold]Statistics[/bold]", border_style="blue")

    def _create_footer(self) -> "Panel":
        """Create footer panel."""
        if not RICH_AVAILABLE:
            return Panel("Footer")

        from rich.align import Align
        last_call = self._stats.get("last_call_time", "N/A")
        if last_call != "N/A" and isinstance(last_call, datetime):
            last_call = last_call.strftime("%H:%M:%S")

        footer_text = Text(f"Last call: {last_call}", style="dim")
        return Panel(Align.center(footer_text))

    def update(self, stats: Dict[str, Any]) -> None:
        """
        Update dashboard with new statistics.

        Args:
            stats: Dictionary of statistics from SavingsLogger.
        """
        if not self._enabled:
            return

        self._stats.update(stats)
        self._stats["last_call_time"] = datetime.now()

        if self._live and RICH_AVAILABLE:
            self._live.update(self._create_layout())

    def log_call(
        self,
        original_tokens: int,
        sent_tokens: int,
        similarity: float,
        hallucination_flags: int,
    ) -> None:
        """
        Log a call to the dashboard.

        Args:
            original_tokens: Original token count.
            sent_tokens: Compressed token count.
            similarity: Semantic similarity score.
            hallucination_flags: Number of hallucination flags.
        """
        if not self._enabled:
            return

        saved = original_tokens - sent_tokens
        savings_pct = (saved / original_tokens * 100) if original_tokens > 0 else 0

        self._stats["total_calls"] += 1
        self._stats["cumulative_tokens_saved"] += saved
        self._stats["cumulative_cost_saved"] += saved * 0.000005
        self._stats["avg_tokens_saved_per_call"] = (
            self._stats["cumulative_tokens_saved"] / self._stats["total_calls"]
        )
        self._stats["hallucination_flags"] += hallucination_flags
        self._stats["last_call_time"] = datetime.now()

        self.update(self._stats)


class DashboardManager:
    """Manages dashboard instances."""

    def __init__(self):
        """Initialize manager."""
        self._dashboards: Dict[str, SlimZeroDashboard] = {}

    def get_or_create(self, name: str = "default") -> SlimZeroDashboard:
        """Get or create a dashboard."""
        if name not in self._dashboards:
            self._dashboards[name] = SlimZeroDashboard()
        return self._dashboards[name]

    def stop_all(self) -> None:
        """Stop all dashboards."""
        for dashboard in self._dashboards.values():
            dashboard.stop()


_default_manager = DashboardManager()


def get_dashboard(name: str = "default") -> SlimZeroDashboard:
    """Get the default dashboard instance."""
    return _default_manager.get_or_create(name)
