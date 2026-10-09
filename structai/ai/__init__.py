"""
StructAI AI Assistance Package.
Provides AI explanations and narrative engineering insights for pre-calculated structural results.
"""

from structai.ai.schemas import AIDesignExplanation
from structai.ai.serializer import serialize_beam_design
from structai.ai.client import AnthropicAIClient, StructAIAIClientError, StructAIConfigurationError
from structai.ai.assistant import explain_beam_design

__all__ = [
    "AIDesignExplanation",
    "serialize_beam_design",
    "AnthropicAIClient",
    "StructAIAIClientError",
    "StructAIConfigurationError",
    "explain_beam_design",
]
