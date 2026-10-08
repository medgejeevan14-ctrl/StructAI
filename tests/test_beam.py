"""
End-to-end integration tests for IS456BeamDesignEngine.
"""

import unittest
from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    FactoredLoads,
    StirrupDetails,
    SupportCondition,
)
from structai.codes.is456.beam import IS456BeamDesignEngine


class TestIS456BeamEngine(unittest.TestCase):

    def test_end_to_end_singly_reinforced_beam_pass(self):
        """Test complete end-to-end beam design for a passing beam section."""
        geom = BeamGeometry(
            b=300.0,
            D=600.0,
            d=550.0,
            span=6000.0,
            support_condition=SupportCondition.SIMPLY_SUPPORTED,
        )
        materials = MaterialProperties(f_ck=25.0, f_y=500.0)
        loads = FactoredLoads(M_u=150.0, V_u=80.0)
        stirrups = StirrupDetails(num_legs=2, bar_diameter=8.0, spacing=150.0)

        engine = IS456BeamDesignEngine(
            geometry=geom,
            materials=materials,
            loads=loads,
            stirrup_details=stirrups,
            stirrup_spacing_provided_mm=150.0,
            main_bar_diameter_mm=20.0,
        )

        res = engine.run_design()

        self.assertTrue(res.is_overall_pass)
        self.assertFalse(res.flexure.is_doubly_reinforced_required)
        self.assertTrue(res.shear.is_section_safe_in_shear)
        self.assertGreater(res.flexure.Ast_req_mm2, 0.0)
        self.assertEqual(res.flexure.xu_max_d_ratio, 0.46)  # Fe 500 => xu_max/d = 0.46

    def test_end_to_end_doubly_reinforced_needed(self):
        """Test end-to-end beam design where Mu exceeds Mu_lim."""
        geom = BeamGeometry(
            b=250.0,
            D=400.0,
            d=350.0,
            span=4000.0,
        )
        materials = MaterialProperties(f_ck=20.0, f_y=415.0)
        # Mu_lim for 250x350 M20 Fe415 ~ 83.4 kNm. Apply Mu = 120 kNm.
        loads = FactoredLoads(M_u=120.0, V_u=40.0)

        engine = IS456BeamDesignEngine(
            geometry=geom,
            materials=materials,
            loads=loads,
        )

        res = engine.run_design()

        self.assertFalse(res.is_overall_pass)
        self.assertTrue(res.flexure.is_doubly_reinforced_required)


if __name__ == "__main__":
    unittest.main()
