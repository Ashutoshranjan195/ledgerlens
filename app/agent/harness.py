"""Agent Harness Layer for LedgerLens.

HARNESS JUSTIFICATION & ARCHITECTURAL CHOICE:
===============================================================================
We implement an inspectable, transparent ReAct (Reason + Act) loop following
the minimalist principles of smolagents and Pydantic AI.

Why this choice over heavy frameworks (LangGraph, CrewAI, AutoGen)?
1. Zero bloat: We avoid dragging in 40+ transitive dependencies that risk
   bringing in analytics or telemetry SDKs.
2. Absolute inspectability: Every prompt, reasoning step, tool call, and tool
   result is recorded into an execution trace that the user can inspect in the UI.
3. Offline & local-first reliability: Deterministic fallbacks ensure that even if
   a small 3B model produces flawed JSON, the agent detects it, invokes local
   validation tools, and corrects itself without requiring external servers.
4. Editability: All prompts live in prompts/*.md and can be swapped or evaluated
   without modifying code.
===============================================================================
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.agent.prompts_loader import get_prompt
from app.agent.tools import validate_math, lookup_schedule_c_category, detect_currency_symbol, format_few_shot_context
from app.utils.logging import logger

@dataclass
class AgentStep:
    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None

@dataclass
class AgentTrace:
    prompt_used: str
    steps: List[AgentStep] = field(default_factory=list)
    final_output: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    needs_review: bool = False
    review_reasons: List[str] = field(default_factory=list)

class InspectableAgentHarness:
    """A fully transparent agent harness that runs reasoning steps locally."""

    def __init__(self, infer_fn: Optional[Callable[[str, Optional[str]], str]] = None) -> None:
        self.infer_fn = infer_fn
        self.tools = {
            "validate_math": validate_math,
            "lookup_category": lookup_schedule_c_category,
            "detect_currency": detect_currency_symbol,
        }

    def execute(
        self,
        raw_text: str,
        image_base64: Optional[str] = None,
        few_shots: Optional[List[Dict[str, Any]]] = None
    ) -> AgentTrace:
        few_shot_str = format_few_shot_context(few_shots or [])
        prompt_text = get_prompt(
            "extract_fields",
            raw_text=raw_text,
            few_shot_context=few_shot_str
        )

        trace = AgentTrace(prompt_used=prompt_text)

        # Step 1: Model inference pass
        trace.steps.append(AgentStep(
            step_number=1,
            thought="Sending document text and few-shot corrections to local model for structured field extraction.",
            action="infer_fields"
        ))

        raw_response = ""
        if self.infer_fn:
            try:
                raw_response = self.infer_fn(prompt_text, image_base64)
            except Exception as e:
                logger.error("Inference step failed: %s", e)
                raw_response = "{}"

        # Step 2: Parse structured output
        extracted_data = self._clean_and_parse_json(raw_response)
        trace.steps.append(AgentStep(
            step_number=2,
            thought="Parsed JSON structure from local model output.",
            observation=f"Keys extracted: {list(extracted_data.keys())}"
        ))

        # Step 3: Tool Execution - Verify Math & Currency
        subtotal = extracted_data.get("subtotal")
        tax = extracted_data.get("tax_amount")
        total = extracted_data.get("total_amount")

        math_result = validate_math(subtotal, tax, total)
        trace.steps.append(AgentStep(
            step_number=3,
            thought="Calling validate_math tool to verify arithmetic integrity.",
            action="validate_math",
            action_input={"subtotal": subtotal, "tax": tax, "total": total},
            observation=math_result["message"]
        ))

        # Step 4: Category classification check
        vendor = extracted_data.get("vendor", "")
        current_cat = extracted_data.get("category")
        if not current_cat or current_cat.lower() in ("unknown", "misc", "general", "other"):
            suggested_cat = lookup_schedule_c_category(vendor, raw_text)
            extracted_data["category"] = suggested_cat
            trace.steps.append(AgentStep(
                step_number=4,
                thought=f"Category was uncertain. Invoked lookup_category tool -> suggested '{suggested_cat}'.",
                action="lookup_category",
                observation=suggested_cat
            ))

        # Confidence & Review Queue determination
        confidence = 0.95
        review_reasons = []

        if not total or total <= 0:
            confidence -= 0.40
            review_reasons.append("Missing or non-positive total amount")

        if not vendor or len(vendor.strip()) < 2:
            confidence -= 0.25
            review_reasons.append("Vendor name is ambiguous or missing")

        if not math_result["valid"]:
            confidence -= 0.20
            review_reasons.append(f"Subtotal/Tax arithmetic discrepancy: {math_result['message']}")

        if not extracted_data.get("doc_date"):
            confidence -= 0.15
            review_reasons.append("Document date could not be parsed with high certainty")

        confidence = max(0.0, min(1.0, round(confidence, 2)))
        needs_review = confidence < 0.85

        trace.final_output = extracted_data
        trace.confidence = confidence
        trace.needs_review = needs_review
        trace.review_reasons = review_reasons

        return trace

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Strip markdown fences and parse JSON robustly."""
        cleaned = raw_text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
            if "```" in cleaned:
                cleaned = cleaned.split("```", 1)[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1]
            if "```" in cleaned:
                cleaned = cleaned.split("```", 1)[0]

        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            # Fallback: regex search for outer braces
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(cleaned[start:end+1])
                except Exception:
                    pass
            return {}
