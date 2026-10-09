"""
Primary AI Assistant Service for StructAI.
"""

import json
import re
from typing import Optional, Dict, Any
from structai.codes.is456.beam import BeamDesignSummary
from structai.ai.schemas import AIDesignExplanation
from structai.ai.serializer import serialize_beam_design
from structai.ai.prompts import SYSTEM_PROMPT, construct_explanation_prompt
from structai.ai.client import AnthropicAIClient, StructAIAIClientError


def _extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely extracts a JSON dictionary payload from raw response text.
    Handles direct JSON, code fences, and surrounding conversational text.
    """
    clean = text.strip()

    # Strategy 1: Direct JSON parse
    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Strategy 2: Code block match ```json { ... } ``` or ``` { ... } ```
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
    if code_block_match:
        try:
            data = json.loads(code_block_match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # Strategy 3: Outermost JSON object match { ... }
    object_match = re.search(r"\{.*\}", clean, re.DOTALL)
    if object_match:
        try:
            data = json.loads(object_match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


def parse_claude_response(raw_text: str) -> AIDesignExplanation:
    """
    Parses narrative JSON text from Claude response into AIDesignExplanation dataclass.
    Safely handles markdown code fences, surrounding commentary text, or non-JSON fallback.
    """
    data = _extract_json_payload(raw_text)

    if data is not None:
        def _get_list(key: str) -> list:
            val = data.get(key, [])
            if isinstance(val, list):
                return [str(item) for item in val]
            return []

        summary = str(data.get("overall_summary", "Calculation evaluation complete."))
        detailed = str(data.get("detailed_explanation", raw_text))

        return AIDesignExplanation(
            overall_summary=summary,
            governing_checks=_get_list("governing_checks"),
            failed_checks=_get_list("failed_checks"),
            warnings=_get_list("warnings"),
            recommendations=_get_list("recommendations"),
            detailed_explanation=detailed,
            raw_response=raw_text,
        )

    return AIDesignExplanation(
        overall_summary="Analysis completed (narrative format).",
        governing_checks=[],
        failed_checks=[],
        warnings=[],
        recommendations=[],
        detailed_explanation=raw_text,
        raw_response=raw_text,
    )


def explain_beam_design(
    summary: BeamDesignSummary,
    client: Optional[AnthropicAIClient] = None,
) -> AIDesignExplanation:
    """
    Main entry point function to generate AI explanation for a BeamDesignSummary.

    Flow:
    1. Preserves summary completely (read-only).
    2. Serializes summary to dict.
    3. Formats system & user prompts.
    4. Invokes Anthropic AI Client.
    5. Parses response into AIDesignExplanation object.
    """
    if client is None:
        client = AnthropicAIClient()

    # Step 1: Serialization (Data Transformation)
    serialized_data = serialize_beam_design(summary)

    # Step 2: Prompt Construction
    user_prompt = construct_explanation_prompt(serialized_data)

    # Step 3: API Call
    raw_response = client.generate_message(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    # Step 4: Parse & Return
    return parse_claude_response(raw_response)
