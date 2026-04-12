"""
SlimZero Intent Extractor Stage (Stage 1)

Parses user prompts to extract structured intent for downstream processing.
Uses spaCy for NLP parsing.
"""

from typing import Optional, Tuple, List
import logging

from slimzero.schemas import IntentSchema, StageInput, StageOutput, OutputFormat

logger = logging.getLogger(__name__)

try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Intent extraction will use fallback mode.")

OUTPUT_FORMAT_KEYWORDS = {
    OutputFormat.TABLE: ["table", "tabular", "spreadsheet", "csv"],
    OutputFormat.LIST: ["list", "enumerate", "items", "bullet points", "numbered"],
    OutputFormat.EXPLAIN: ["explain", "describe", "what is", "how does", "why", "understand", "what's"],
    OutputFormat.CODE: ["code", "function", "class", "script", "implement", "write code", "program", "closure"],
}

FILLER_PHRASES = [
    "please", "could you", "would you", "can you", "kindly",
    "if you could", "i was wondering", "i'd like to",
]


class IntentExtractor:
    """
    Extracts structured intent from raw user prompts.

    Uses spaCy for NLP parsing when available.
    Falls back to simple keyword extraction if spaCy is unavailable.
    """

    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize IntentExtractor.

        Args:
            model: spaCy model name. Defaults to en_core_web_sm.
        """
        self.model_name = model
        self._nlp: Optional[Language] = None

        if SPACY_AVAILABLE:
            try:
                self._nlp = spacy.load(model)
                logger.info(f"Loaded spaCy model: {model}")
            except OSError:
                logger.warning(
                    f"spaCy model '{model}' not found. "
                    f"Install with: python -m spacy download {model}"
                )
                self._nlp = None

    def _is_available(self) -> bool:
        """Check if spaCy is available and loaded."""
        return SPACY_AVAILABLE and self._nlp is not None

    def _extract_entities(self, doc) -> Tuple[str, ...]:
        """Extract named entities and noun chunks from spaCy doc."""
        entities = []

        for ent in doc.ents:
            if ent.label_ not in ("CARDINAL", "ORDINAL", "QUANTITY"):
                entities.append(ent.text.strip())

        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if chunk_text not in entities and len(chunk_text) > 2:
                entities.append(chunk_text)

        return tuple(set(entities))

    def _extract_core_task(self, doc) -> str:
        """Extract the core task/action from spaCy doc."""
        root = None
        for token in doc:
            if token.dep_ == "ROOT":
                root = token
                break

        if root:
            core_parts = [root.text]

            for child in root.children:
                if child.dep_ in ("dobj", "pobj", "nsubj", "attr"):
                    core_parts.append(child.text)
                    for grandchild in child.subtree:
                        if grandchild.dep_ in ("amod", "compound", "det"):
                            core_parts.insert(0, grandchild.text)

            core_task = " ".join(filter(None, core_parts))
            if core_task:
                return core_task.strip()

        tokens = [t.text for t in doc if not t.is_stop and not t.is_punct]
        return " ".join(tokens[:10]) if tokens else doc.text

    def _detect_output_format(self, text: str) -> OutputFormat:
        """Detect the expected output format from prompt keywords."""
        text_lower = text.lower()

        for format_type, keywords in OUTPUT_FORMAT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return format_type

        return OutputFormat.GENERAL

    def _extract_constraints(self, doc) -> Tuple[str, ...]:
        """Extract constraints and conditional phrases from prompt."""
        constraints = []

        negation_words = {"not", "no", "never", "don't", "don't", "doesn't", "without", "exclude", "avoid"}
        modal_words = {"must", "should", "need", "require", "have to"}

        for i, token in enumerate(doc):
            token_text = token.text.lower()

            if token_text in negation_words:
                constraint = f"NOT {doc[i + 1].text}" if i + 1 < len(doc) else token_text
                constraints.append(constraint.strip())

            if token_text in modal_words:
                for child in token.head.subtree:
                    if child.i > token.i:
                        constraint = f"MUST {token.head.text} {' '.join([t.text for t in doc[token.i:child.i + 1]])}"
                        constraints.append(constraint.strip())
                        break

        conditional_keywords = ["if", "when", "unless", "provided that", "assuming"]
        text_lower = doc.text.lower()
        for keyword in conditional_keywords:
            if keyword in text_lower:
                idx = text_lower.index(keyword)
                end = min(idx + 50, len(doc.text))
                snippet = doc.text[idx:end].split(".")[0]
                if snippet:
                    constraints.append(f"CONDITIONAL: {snippet.strip()}")

        return tuple(set(constraints))

    def _strip_filler(self, text: str) -> str:
        """Remove filler phrases from prompt text."""
        result = text
        for phrase in FILLER_PHRASES:
            result = result.lower().replace(phrase.lower(), "")
        return " ".join(result.split())

    def extract(self, prompt: str) -> IntentSchema:
        """
        Extract structured intent from a prompt.

        Args:
            prompt: The raw user prompt to analyze.

        Returns:
            IntentSchema with extracted intent components.
        """
        if not prompt or not prompt.strip():
            return IntentSchema(
                core_task="",
                entities=(),
                output_format=OutputFormat.UNKNOWN,
                constraints=(),
                raw_prompt=prompt,
            )

        stripped_prompt = self._strip_filler(prompt)

        if self._is_available() and self._nlp is not None:
            try:
                doc = self._nlp(stripped_prompt)

                core_task = self._extract_core_task(doc)
                entities = self._extract_entities(doc)
                output_format = self._detect_output_format(stripped_prompt)
                constraints = self._extract_constraints(doc)

                return IntentSchema(
                    core_task=core_task,
                    entities=entities,
                    output_format=output_format,
                    constraints=constraints,
                    raw_prompt=prompt,
                )
            except Exception as e:
                logger.warning(f"spaCy processing failed: {e}. Using fallback.")

        return self._fallback_extract(stripped_prompt, prompt)

    def _fallback_extract(self, stripped_prompt: str, original_prompt: str) -> IntentSchema:
        """Fallback extraction when spaCy is unavailable."""
        words = stripped_prompt.lower().split()

        verbs = {"explain", "describe", "write", "create", "generate", "list", "find", "show", "tell", "give"}
        action_words = [w for w in words if w in verbs]

        if action_words:
            core_task = f"{action_words[0]} {stripped_prompt.split(action_words[0])[1][:50] if action_words[0] in stripped_prompt else ''}"
        else:
            core_task = stripped_prompt[:50] if len(stripped_prompt) > 50 else stripped_prompt

        entities = tuple(word for word in words if len(word) > 4)[:5]
        output_format = self._detect_output_format(stripped_prompt)

        return IntentSchema(
            core_task=core_task.strip(),
            entities=entities,
            output_format=output_format,
            constraints=(),
            raw_prompt=original_prompt,
        )

    def process(self, inp: StageInput) -> StageOutput:
        """
        Process a StageInput to extract intent.

        Args:
            inp: StageInput containing the prompt.

        Returns:
            StageOutput with modified prompt (unchanged) and intent in metadata.
        """
        intent = self.extract(inp.prompt)

        return StageOutput(
            prompt=inp.prompt,
            modified=False,
            notes=f"Extracted intent: {intent.core_task[:50]}...",
            metadata={
                "intent": intent.to_dict(),
                "spacy_available": self._is_available(),
            },
        )
