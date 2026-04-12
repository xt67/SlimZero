"""
SlimZero Hallucination Flagger (post-processing)

Detects confident assertions in responses that correspond to high-risk query types.
Uses 80-pattern heuristic library for date assertions, numeric specifics, citations.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

DATE_ASSERTIONS = [
    r"\bin\s+19\d{2}\b",
    r"\bin\s+20\d{2}\b",
    r"\bjanuary\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bfebruary\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bmarch\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bapril\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bmay\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bjune\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bjuly\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\baugust\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bseptember\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\boctober\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bnovember\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\bdecember\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}\b",
    r"\byesterday\b",
    r"\btoday\b",
    r"\btomorrow\b",
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
]

NUMERIC_SPECIFICS = [
    r"\b\d+(?:\.\d+)?\s*%\b",
    r"\b\d{1,3}(?:,\d{3})+(?:,\d{3})*\b",
    r"\b\d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)\b",
    r"\bexactly\s+\d+\b",
    r"\bapproximately\s+\d+\b",
    r"\babout\s+\d+\b",
    r"\broughly\s+\d+\b",
    r"\bonly\s+\d+\b",
    r"\bmore\s+than\s+\d+\b",
    r"\bfewer\s+than\s+\d+\b",
    r"\bat\s+least\s+\d+\b",
    r"\bat\s+most\s+\d+\b",
]

CITATION_PHRASES = [
    r"\bacademic\s+(?:paper|journal|article|study)\b",
    r"\bpeer-?reviewed\b",
    r"\bpublished\s+in\s+\d{4}\b",
    r"\bstudy\s+published\b",
    r"\bresearch\s+shows\b",
    r"\baccording\s+to\s+research\b",
    r"\bthe\s+study\s+(?:found|shows|indicates|suggests|report)\b",
    r"\barxiv\s*:\s*\w+\b",
    r"\bdoi\s*:\s*[\w./]+\b",
    r"\bjournal\s+(?:of|published)\b",
]

AUTHORITY_CLAIMS = [
    r"\bscientists?\s+(?:say|believe|think|discovered|found)\b",
    r"\bexperts?\s+(?:say|believe|think|suggest|claim)\b",
    r"\bresearchers?\s+(?:say|found|discovered|believe)\b",
    r"\bdoctors?\s+(?:say|recommend|suggest|believe)\b",
    r"\bstudies?\s+(?:show|indicate|suggest|prove)\b",
    r"\bit\s+is\s+(?:known|proven|established|fact)\b",
    r"\bit\s+has\s+been\s+(?:proven|shown|demonstrated)\b",
    r"\baccording\s+to\s+(?:science|scientists|experts)\b",
]

STATISTICAL_CLAIMS = [
    r"\bstatistically\s+(?:significant|significant)\b",
    r"\b(p-?value|p\s*value)\s*<?=\s*\d+\.?\d*\b",
    r"\bconfidence\s+interval\b",
    r"\bcorrelation\s+between\b",
    r"\bcausation\b",
    r"\bcontrolled\s+(?:study|trial|experiment)\b",
    r"\brandomized\s+(?:controlled\s+)?trial\b",
]

UNVERIFIABLE_CERTAINTY = [
    r"\bwill\s+(?:definitely|certainly|surely|absolutely)\b",
    r"\bwill\s+never\b",
    r"\bwill\s+always\b",
    r"\bguaranteed\s+to\b",
    r"\b100%\s+(?:effective|safe|accurate|correct)\b",
    r"\bproven\s+(?:to|that)\b",
    r"\balways\s+(?:the\s+case|true|correct)\b",
    r"\bnever\s+(?:happens|occurs|true)\b",
]

ALL_PATTERNS = DATE_ASSERTIONS + NUMERIC_SPECIFICS + CITATION_PHRASES + AUTHORITY_CLAIMS + STATISTICAL_CLAIMS + UNVERIFIABLE_CERTAINTY


class HallucinationFlagger:
    """
    Detects confident assertions in responses that may be hallucinations.

    Uses 80-pattern heuristic library for date assertions, numeric specifics,
    citation phrases, and authority claims. No second API call - purely local.
    False positives acceptable - SlimZero errs toward flagging.
    """

    def __init__(self):
        """Initialize HallucinationFlagger."""
        self._compiled_patterns: List[Tuple[re.Pattern, str]] = []
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Compile all regex patterns with category labels."""
        categories = {
            "date_assertion": DATE_ASSERTIONS,
            "numeric_specific": NUMERIC_SPECIFICS,
            "citation_phrase": CITATION_PHRASES,
            "authority_claim": AUTHORITY_CLAIMS,
            "statistical_claim": STATISTICAL_CLAIMS,
            "unverifiable_certainty": UNVERIFIABLE_CERTAINTY,
        }

        for category, patterns in categories.items():
            for pattern in patterns:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self._compiled_patterns.append((compiled, category))
                except re.error as e:
                    logger.warning(f"Invalid pattern '{pattern}': {e}")

    def _find_matches(self, text: str) -> List[Dict[str, Any]]:
        """Find all pattern matches in text."""
        matches = []

        for pattern, category in self._compiled_patterns:
            for match in pattern.finditer(text):
                matches.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "category": category,
                })

        matches.sort(key=lambda x: x["start"])  # type: ignore[arg-type, return-value]
        return matches

    def flag(self, response: str) -> Dict[str, Any]:
        """
        Flag potential hallucinations in response.

        Args:
            response: LLM response text.

        Returns:
            Dict with flagged segments and metadata.
        """
        if not response:
            return {
                "has_flags": False,
                "flags": [],
                "total_flags": 0,
                "categories": {},
            }

        matches = self._find_matches(response)

        categories: Dict[str, int] = {}
        for match in matches:
            cat = match["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "has_flags": len(matches) > 0,
            "flags": matches,
            "total_flags": len(matches),
            "categories": categories,
        }

    def flag_with_context(
        self,
        response: str,
        context_window: int = 50,
    ) -> Dict[str, Any]:
        """
        Flag hallucinations with surrounding context.

        Args:
            response: LLM response text.
            context_window: Characters of context around each match.

        Returns:
            Dict with flagged segments including context.
        """
        if not response:
            return {
                "has_flags": False,
                "flags": [],
                "total_flags": 0,
            }

        matches = self._find_matches(response)
        flags_with_context = []

        for match in matches:
            start = max(0, match["start"] - context_window)
            end = min(len(response), match["end"] + context_window)
            context = response[start:end]

            flags_with_context.append({
                "text": match["text"],
                "start": match["start"],
                "end": match["end"],
                "category": match["category"],
                "context": context,
            })

        return {
            "has_flags": len(flags_with_context) > 0,
            "flags": flags_with_context,
            "total_flags": len(flags_with_context),
        }
