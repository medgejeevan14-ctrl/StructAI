"""
Offline Unit & Integration Tests for StructAI Streamlit UI Interface.
All tests are 100% offline with zero external network or live API dependencies.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    FactoredLoads,
    StirrupDetails,
    SupportCondition,
    CheckStatus,
)
from structai.codes.is456.beam import IS456BeamDesignEngine
from structai.ai.schemas import AIDesignExplanation
from app import format_status_badge, explain_beam_design, AnthropicAIClient


class TestStructAIUIIntegration(unittest.TestCase):

    def setUp(self):
        self.geom = BeamGeometry(
            b=300.0,
            D=600.0,
            d=550.0,
            d_prime=40.0,
            span=6000.0,
            support_condition=SupportCondition.SIMPLY_SUPPORTED,
        )
        self.materials = MaterialProperties(
            f_ck=25.0,
            f_y=500.0,
            f_yv=500.0,
            is_hysd=True,
        )
        self.loads = FactoredLoads(
            M_u=150.0,
            V_u=80.0,
            T_u=0.0,
        )
        self.stirrups = StirrupDetails(
            num_legs=2,
            bar_diameter=8.0,
            spacing=150.0,
        )
        self.engine = IS456BeamDesignEngine(
            geometry=self.geom,
            materials=self.materials,
            loads=self.loads,
            stirrup_details=self.stirrups,
            stirrup_spacing_provided_mm=150.0,
            main_bar_diameter_mm=20.0,
        )
        self.summary = self.engine.run_design()

    def test_status_badge_formatting(self):
        """1. Test HTML status badge formatting for all CheckStatus enums."""
        pass_badge = format_status_badge(CheckStatus.PASS)
        fail_badge = format_status_badge(CheckStatus.FAIL)
        warn_badge = format_status_badge(CheckStatus.WARNING)
        na_badge = format_status_badge(CheckStatus.NOT_APPLICABLE)
        ni_badge = format_status_badge(CheckStatus.NOT_IMPLEMENTED)

        self.assertIn("PASS", pass_badge)
        self.assertIn("#1e7e34", pass_badge)
        self.assertIn("FAIL", fail_badge)
        self.assertIn("#bd2130", fail_badge)
        self.assertIn("WARNING", warn_badge)
        self.assertIn("NOT_APPLICABLE", na_badge)
        self.assertIn("NOT_IMPLEMENTED", ni_badge)

    def test_ui_inputs_engine_pipeline(self):
        """2. Test UI input parameters construct valid domain objects and generate summary."""
        self.assertTrue(self.summary.is_overall_pass)
        self.assertEqual(self.summary.geometry.b, 300.0)
        self.assertEqual(self.summary.materials.f_ck, 25.0)
        self.assertEqual(self.summary.loads.M_u, 150.0)
        self.assertGreater(self.summary.flexure.governing_Ast_mm2, 0.0)
        self.assertGreater(self.summary.shear.tau_v_Nmm2, 0.0)

    def test_ui_audit_table_data_extraction(self):
        """3. Test extraction of code check audit rows consumed by UI table."""
        code_checks = self.summary.detailing.code_checks
        self.assertGreater(len(code_checks), 0)

        for chk in code_checks:
            self.assertIsNotNone(chk.check_name)
            self.assertIsNotNone(chk.clause)
            self.assertIsNotNone(chk.status)
            self.assertIsInstance(chk.demand, (int, float))
            self.assertIsInstance(chk.capacity, (int, float))

    def test_ui_mocked_ai_explanation_generation(self):
        """4. Test UI integration with explain_beam_design using mocked Anthropic client."""
        mock_client = MagicMock(spec=AnthropicAIClient)
        mock_client.generate_message.return_value = """{
            "overall_summary": "Beam section passes all IS 456 checks.",
            "governing_checks": ["Flexure capacity"],
            "failed_checks": [],
            "warnings": [],
            "recommendations": ["Provide 3-20mm bars."],
            "detailed_explanation": "Flexural and shear designs satisfy code criteria."
        }"""

        res = explain_beam_design(self.summary, client=mock_client)
    def test_provided_stirrup_spacing_exceeded_fails(self):
        """5. Test high shear scenario where provided stirrup spacing exceeds required strength spacing."""
        # Applied Vu = 250 kN produces net shear force requiring sv_calc ~ 90 mm
        loads_high_shear = FactoredLoads(M_u=150.0, V_u=250.0, T_u=0.0)
        engine = IS456BeamDesignEngine(
            geometry=self.geom,
            materials=self.materials,
            loads=loads_high_shear,
            stirrup_details=self.stirrups,
            stirrup_spacing_provided_mm=200.0,  # 200mm provided > ~90mm required for strength
            main_bar_diameter_mm=20.0,
        )
        summary = engine.run_design()
        self.assertFalse(summary.is_overall_pass)

        strength_check = [c for c in summary.detailing.code_checks if "Shear Strength" in c.check_name][0]
        self.assertEqual(strength_check.status, CheckStatus.FAIL)
        self.assertIn("Provided stirrup spacing", strength_check.message)

    def test_excessive_stirrup_spacing_code_limit_fails(self):
        """6. Test scenario where provided stirrup spacing exceeds maximum code permissible limit."""
        engine = IS456BeamDesignEngine(
            geometry=self.geom,
            materials=self.materials,
            loads=self.loads,
            stirrup_details=self.stirrups,
            stirrup_spacing_provided_mm=400.0,  # 400mm > 300mm max code limit
            main_bar_diameter_mm=20.0,
        )
        summary = engine.run_design()
        self.assertFalse(summary.is_overall_pass)

        max_spacing_check = [c for c in summary.detailing.code_checks if "Code Limit" in c.check_name][0]
        self.assertEqual(max_spacing_check.status, CheckStatus.FAIL)

    def test_ui_failure_banner_triggers_on_excessive_moment_and_shear(self):
        """7. Test that excessive moment (Mu > Mu_lim) or shear (tau_v > tau_c_max) triggers failure state."""
        # 1. Excessive moment (Mu = 350 kNm > Mu_lim = 303.12 kNm)
        loads_ex_m = FactoredLoads(M_u=350.0, V_u=50.0)
        engine_m = IS456BeamDesignEngine(geometry=self.geom, materials=self.materials, loads=loads_ex_m)
        sum_m = engine_m.run_design()
        self.assertFalse(sum_m.is_overall_pass)
        self.assertTrue(sum_m.flexure.is_doubly_reinforced_required)

        # 2. Excessive shear (tau_v = 3.636 N/mm² > tau_c_max = 3.10 N/mm² for M25)
        loads_ex_v = FactoredLoads(M_u=50.0, V_u=600.0)
        engine_v = IS456BeamDesignEngine(geometry=self.geom, materials=self.materials, loads=loads_ex_v)
        sum_v = engine_v.run_design()
        self.assertFalse(sum_v.is_overall_pass)
        self.assertFalse(sum_v.shear.is_section_safe_in_shear)


if __name__ == "__main__":
    unittest.main()
