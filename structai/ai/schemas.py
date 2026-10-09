"""
Schemas and dataclasses for StructAI AI assistance layer.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AIDesignExplanation:
    """
    Structured AI explanation response object for an IS 456 beam design result.
    """
    overall_summary: str
    governing_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    detailed_explanation: str = ""
    disclaimer: str = (
        "StructAI AI Assistant provides explanatory rationale for pre-calculated IS 456:2000 results. "
        "It does not perform engineering calculations and is not a substitute for independent "
        "verification by a Licensed Professional Engineer."
    )
    raw_response: Optional[str] = None
