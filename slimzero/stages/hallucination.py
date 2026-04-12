"""
SlimZero Hallucination Risk Scorer Stage (Stage 7)

Classifies query hallucination risk and injects uncertainty instructions.
Uses 50-rule heuristic classifier with regex and keyword patterns.
"""

import re
import logging
from typing import List, Optional, Tuple

from slimzero.schemas import StageInput, StageOutput, HallucinationRiskTier

logger = logging.getLogger(__name__)

DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bin\s+20\d{2}\b",
    r"\bin\s+19\d{2}\b",
    r"\byesterday\b",
    r"\btoday\b",
    r"\btomorrow\b",
    r"\blast\s+(week|month|year)\b",
    r"\bnext\s+(week|month|year)\b",
]

NUMBER_PATTERNS = [
    r"\b\d+(?:\.\d+)?%\b",
    r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b",
    r"\b(million|billion|trillion|thousand)\b",
    r"\bapproximately\s+\d+\b",
    r"\bbetween\s+\d+\s+and\s+\d+\b",
    r"\bexactly\s+\d+\b",
    r"\bonly\s+\d+\b",
]

CITATION_PATTERNS = [
    r"\b(study|research|paper|article|report|journal)\s+(?:from|published|published in|by)\b",
    r"\bacademic\s+(?:paper|journal|conference)\b",
    r"\baccording\s+to\s+(?:research|study|experts|scientists)\b",
    r"\bthe\s+(?:study|research|paper)\s+(?:shows|indicates|suggests|reports)\b",
    r"\b(peer-reviewed|peer reviewed)\b",
    r"\barxiv\b",
    r"\bdoi[:/]\b",
    r"\b[0-9a-f]{10,}\b",
]

RECENCY_PATTERNS = [
    r"\b(latest|most recent|newest|recently)\b",
    r"\b(current|up-to-date)\b",
    r"\b(202[3-9]|203\d)\b",
    r"\b(breaking|just\s+happened|emerging)\b",
    r"\bnowhere\b.*\b(says|reports|states)\b",
]

ENTITY_VERIFIABLE_PATTERNS = [
    r"\bCEO\s+of\b",
    r"\bfounder\s+of\b",
    r"\bpresident\s+of\b",
    r"\blocated\s+in\b",
    r"\bcountry\s+of\b",
    r"\bpopulation\s+of\b",
    r"\bcapital\s+of\b",
    r"\bweather\s+in\b",
    r"\btemperature\s+in\b",
    r"\bstock\s+price\b",
    r"\bcompany\s+revenue\b",
]

DEFAULT_INSTRUCTIONS = {
    HallucinationRiskTier.HIGH: "If uncertain, say you don't know. Don't guess specific dates, numbers, or citations.",
    HallucinationRiskTier.MEDIUM: "Verify claims before stating. Provide uncertainty markers like 'typically' or 'often'.",
    HallucinationRiskTier.LOW: "",
}


class HallucinationRiskScorer:
    """
    Scores hallucination risk for queries and injects uncertainty instructions.

    Uses 50-rule heuristic classifier (regex + keyword patterns).
    No model inference - purely local signal processing.
    """

    def __init__(
        self,
        high_risk_instructions: Optional[str] = None,
        medium_risk_instructions: Optional[str] = None,
    ):
        """
        Initialize HallucinationRiskScorer.

        Args:
            high_risk_instructions: Custom instructions for HIGH risk queries.
            medium_risk_instructions: Custom instructions for MEDIUM risk queries.
        """
        self.high_risk_instructions = high_risk_instructions or DEFAULT_INSTRUCTIONS[HallucinationRiskTier.HIGH]
        self.medium_risk_instructions = medium_risk_instructions or DEFAULT_INSTRUCTIONS[HallucinationRiskTier.MEDIUM]

        self._high_patterns: List[re.Pattern] = []
        self._medium_patterns: List[re.Pattern] = []
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Compile all regex patterns."""
        for pattern in DATE_PATTERNS:
            self._high_patterns.append(re.compile(pattern, re.IGNORECASE))

        for pattern in NUMBER_PATTERNS:
            self._high_patterns.append(re.compile(pattern, re.IGNORECASE))

        for pattern in CITATION_PATTERNS:
            self._high_patterns.append(re.compile(pattern, re.IGNORECASE))

        for pattern in RECENCY_PATTERNS:
            self._high_patterns.append(re.compile(pattern, re.IGNORECASE))

        for pattern in ENTITY_VERIFIABLE_PATTERNS:
            self._medium_patterns.append(re.compile(pattern, re.IGNORECASE))

        VERIFIABLE_KEYWORDS = [
            "who is", "who was", "what is", "what was",
            "where is", "where was", "when did", "how many",
            "population", "area", "gdp", "revenue", "profit",
            "height", "weight", "distance", "size",
        ]
        for keyword in VERIFIABLE_KEYWORDS:
            self._medium_patterns.append(re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE))

    def _count_matches(self, text: str, patterns: List[re.Pattern]) -> int:
        """Count number of pattern matches in text."""
        count = 0
        for pattern in patterns:
            if pattern.search(text):
                count += 1
        return count

    def _classify(self, text: str) -> HallucinationRiskTier:
        """
        Classify hallucination risk tier for text.

        Args:
            text: Text to classify.

        Returns:
            HallucinationRiskTier classification.
        """
        high_matches = self._count_matches(text, self._high_patterns)
        medium_matches = self._count_matches(text, self._medium_patterns)

        if high_matches >= 1:
            return HallucinationRiskTier.HIGH

        if medium_matches >= 2:
            return HallucinationRiskTier.MEDIUM

        if medium_matches == 1 and len(text.split()) < 10:
            return HallucinationRiskTier.MEDIUM

        return HallucinationRiskTier.LOW

    def score(self, text: str) -> Tuple[HallucinationRiskTier, int, int]:
        """
        Score hallucination risk for text.

        Args:
            text: Text to score.

        Returns:
            Tuple of (risk_tier, high_matches, medium_matches).
        """
        if not text or not text.strip():
            return HallucinationRiskTier.MEDIUM, 0, 0

        tier = self._classify(text)
        high_matches = self._count_matches(text, self._high_patterns)
        medium_matches = self._count_matches(text, self._medium_patterns)

        return tier, high_matches, medium_matches

    def get_instructions(self, tier: HallucinationRiskTier) -> str:
        """
        Get uncertainty instructions for risk tier.

        Args:
            tier: Risk tier.

        Returns:
            Uncertainty instructions string.
        """
        if tier == HallucinationRiskTier.HIGH:
            return self.high_risk_instructions
        elif tier == HallucinationRiskTier.MEDIUM:
            return self.medium_risk_instructions
        return ""

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to score hallucination risk.

        Args:
            inp: StageInput containing prompt.

        Returns:
            StageOutput with risk classification and instructions.
        """
        text = inp.prompt
        tier, high_matches, medium_matches = self.score(text)

        instructions = self.get_instructions(tier)

        return StageOutput(
            prompt=inp.prompt,
            modified=tier != HallucinationRiskTier.LOW,
            notes=f"Risk: {tier.value} (high={high_matches}, medium={medium_matches})",
            metadata={
                "risk_tier": tier.value,
                "high_matches": high_matches,
                "medium_matches": medium_matches,
                "instructions": instructions,
                "is_high_risk": tier == HallucinationRiskTier.HIGH,
                "is_medium_risk": tier == HallucinationRiskTier.MEDIUM,
                "is_low_risk": tier == HallucinationRiskTier.LOW,
            },
        )
