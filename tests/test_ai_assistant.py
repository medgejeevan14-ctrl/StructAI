"""
Offline Unit Tests for StructAI AI Assistance Layer.
All API calls are mocked using unittest.mock. No real API calls or costs incurred.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from structai.core.datatypes import BeamGeometry, MaterialProperties, FactoredLoads, SupportCondition, CheckStatus
from structai.codes.is456.beam import IS456BeamDesignEngine
from structai.ai.schemas import AIDesignExplanation
from structai.ai.serializer import serialize_beam_design
from structai.ai.prompts import construct_explanation_prompt, SYSTEM_PROMPT
from structai.ai.client import AnthropicAIClient, StructAIConfigurationError, StructAIAIClientError
from dataclasses import FrozenInstanceError
from structai.ai.assistant import explain_beam_design, parse_claude_response


class TestStructAIAIAssistant(unittest.TestCase):

    def setUp(self):
        geom = BeamGeometry(b=300.0, D=600.0, d=550.0, span=6000.0, support_condition=SupportCondition.SIMPLY_SUPPORTED)
        materials = MaterialProperties(f_ck=25.0, f_y=500.0)
        loads = FactoredLoads(M_u=150.0, V_u=80.0)
        engine = IS456BeamDesignEngine(geom, materials, loads)
        self.summary = engine.run_design()

    def test_beam_design_summary_serialization(self):
        """1. Test BeamDesignSummary serialization produces expected dictionary structure."""
        data = serialize_beam_design(self.summary)
        self.assertIsInstance(data, dict)
        self.assertIn("geometry", data)
        self.assertIn("materials", data)
        self.assertIn("factored_loads", data)
        self.assertIn("flexure_design", data)
        self.assertIn("shear_design", data)
        self.assertIn("detailing_and_serviceability", data)
        self.assertIn("overall_status", data)

    def test_required_engineering_fields_preserved(self):
        """2. Test numerical engineering values are preserved accurately during serialization."""
        data = serialize_beam_design(self.summary)
        self.assertEqual(data["geometry"]["width_b_mm"], 300.0)
        self.assertEqual(data["materials"]["f_ck_Nmm2"], 25.0)
        self.assertEqual(data["materials"]["f_y_Nmm2"], 500.0)
        self.assertEqual(data["factored_loads"]["bending_moment_M_u_kNm"], 150.0)
        self.assertEqual(data["factored_loads"]["shear_force_V_u_kN"], 80.0)

    def test_clause_references_preserved(self):
        """3. Test IS 456 clause references are preserved in serialized data."""
        data = serialize_beam_design(self.summary)
        flex_clauses = data["flexure_design"]["clauses"]
        shear_clauses = data["shear_design"]["clauses"]
        code_checks = data["detailing_and_serviceability"]["code_checks"]

        self.assertTrue(any("Clause 38.1" in cl for cl in flex_clauses))
        self.assertTrue(any("Clause 40.1" in cl for cl in shear_clauses))
        self.assertTrue(any("Cl 26.5.1.1 (a)" in chk["clause"] for chk in code_checks))

    def test_statuses_preserved(self):
        """4. Test PASS/FAIL/WARNING/NOT_IMPLEMENTED check statuses are preserved."""
        data = serialize_beam_design(self.summary)
        code_checks = data["detailing_and_serviceability"]["code_checks"]
        statuses = [chk["status"] for chk in code_checks]

        self.assertIn("PASS", statuses)
        self.assertIn("NOT_IMPLEMENTED", statuses)

    def test_prompt_construction(self):
        """5. Test prompt construction incorporates rules and serialized json context."""
        data = serialize_beam_design(self.summary)
        user_prompt = construct_explanation_prompt(data)

        self.assertIn("IS 456", SYSTEM_PROMPT)
        self.assertIn("must NOT recalculate", SYSTEM_PROMPT)
        self.assertIn("300.0", user_prompt)
        self.assertIn("flexure_design", user_prompt)

    def test_missing_api_key_handling(self):
        """6. Test missing ANTHROPIC_API_KEY environment variable raises clear configuration error."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(StructAIConfigurationError) as ctx:
                AnthropicAIClient()
            self.assertIn("ANTHROPIC_API_KEY", str(ctx.exception))

    def test_mocked_successful_claude_response(self):
        """7 & 9. Test successful mocked Claude API response handling and AIDesignExplanation creation."""
        mock_client = MagicMock(spec=AnthropicAIClient)
        mock_response_json = """{
            "overall_summary": "Beam section is structurally adequate for applied loads.",
            "governing_checks": ["Minimum Tension Reinforcement", "Maximum Stirrup Spacing"],
            "failed_checks": [],
            "warnings": [],
            "recommendations": ["Provide 3-20mm bars."],
            "detailed_explanation": "Flexural design capacity exceeds applied moment M_u = 150 kNm."
        }"""
        mock_client.generate_message.return_value = mock_response_json

        res = explain_beam_design(self.summary, client=mock_client)

        self.assertIsInstance(res, AIDesignExplanation)
        self.assertEqual(res.overall_summary, "Beam section is structurally adequate for applied loads.")
        self.assertEqual(len(res.governing_checks), 2)
        self.assertEqual(len(res.failed_checks), 0)
        self.assertIn("IS 456:2000", res.disclaimer)
        mock_client.generate_message.assert_called_once()

    def test_invalid_or_empty_mocked_response_handling(self):
        """8. Test handling of invalid or empty narrative response."""
        mock_client = MagicMock(spec=AnthropicAIClient)
        mock_client.generate_message.return_value = "Unstructured narrative text from model without JSON formatting."

        res = explain_beam_design(self.summary, client=mock_client)

        self.assertIsInstance(res, AIDesignExplanation)
        self.assertIn("Unstructured narrative text", res.detailed_explanation)

    def test_deterministic_summary_immutability(self):
        """10. Verify deterministic BeamDesignSummary is strictly unmodified by AI layer and is frozen."""
        orig_ast = self.summary.flexure.governing_Ast_mm2
        orig_tau_v = self.summary.shear.tau_v_Nmm2
        orig_pass = self.summary.is_overall_pass

        mock_client = MagicMock(spec=AnthropicAIClient)
        mock_client.generate_message.return_value = '{"overall_summary": "Test OK"}'
        explain_beam_design(self.summary, client=mock_client)

        self.assertEqual(self.summary.flexure.governing_Ast_mm2, orig_ast)
        self.assertEqual(self.summary.shear.tau_v_Nmm2, orig_tau_v)
        self.assertEqual(self.summary.is_overall_pass, orig_pass)

        # Verify instance level immutability raises FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):
            self.summary.is_overall_pass = False

    def test_parse_claude_response_with_surrounding_commentary_and_fences(self):
        """11. Test parsing JSON surrounded by conversational text and markdown code blocks."""
        raw = """Here is the design explanation you requested:
```json
{
    "overall_summary": "Beam design meets all IS 456 requirements.",
    "governing_checks": ["Flexural Capacity"],
    "failed_checks": [],
    "warnings": [],
    "recommendations": ["Use M25 concrete."],
    "detailed_explanation": "Detailed clause explanation."
}
```
Hope this structural evaluation helps!"""
        res = parse_claude_response(raw)
        self.assertEqual(res.overall_summary, "Beam design meets all IS 456 requirements.")
        self.assertEqual(res.governing_checks, ["Flexural Capacity"])
        self.assertEqual(res.recommendations, ["Use M25 concrete."])

    def test_parse_claude_response_non_dict_json_rejection(self):
        """12. Test rejecting non-dictionary JSON payloads safely."""
        raw = "[1, 2, 3]"
        res = parse_claude_response(raw)
        self.assertEqual(res.overall_summary, "Analysis completed (narrative format).")
        self.assertEqual(res.detailed_explanation, raw)


if __name__ == "__main__":
    unittest.main()
