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

    def test_end_to_end_excessive_shear_stress_fails(self):
        """Test end-to-end design where tau_v > tau_c_max triggers overall failure."""
        geom = BeamGeometry(b=200.0, D=400.0, d=350.0, span=4000.0)
        materials = MaterialProperties(f_ck=20.0, f_y=415.0)
        loads = FactoredLoads(M_u=50.0, V_u=200.0)  # tau_v = 200,000 / (200*350) = 2.857 N/mm² > tau_c_max (2.80)

        engine = IS456BeamDesignEngine(geometry=geom, materials=materials, loads=loads)
        res = engine.run_design()

        self.assertFalse(res.is_overall_pass)
        self.assertFalse(res.shear.is_section_safe_in_shear)

    def test_end_to_end_insufficient_ast_min_fails(self):
        """Test end-to-end design where provided Ast < Ast_min triggers overall failure."""
        geom = BeamGeometry(b=300.0, D=600.0, d=550.0, span=6000.0)
        materials = MaterialProperties(f_ck=25.0, f_y=500.0)
        loads = FactoredLoads(M_u=50.0, V_u=30.0)

        engine = IS456BeamDesignEngine(
            geometry=geom,
            materials=materials,
            loads=loads,
            Ast_provided_mm2=150.0,  # 150 mm² < Ast_min (280.5 mm²)
        )
        res = engine.run_design()

        self.assertFalse(res.is_overall_pass)


class TestDatatypeValidation(unittest.TestCase):

    def test_beam_geometry_invalid_inputs(self):
        """Test that invalid beam geometry values raise ValueError."""
        with self.assertRaises(ValueError):
            BeamGeometry(b=300.0, D=600.0, d=550.0, d_prime=-10.0)
        with self.assertRaises(ValueError):
            BeamGeometry(b=300.0, D=600.0, d=550.0, d_prime=600.0)
        with self.assertRaises(ValueError):
            BeamGeometry(b=300.0, D=600.0, d=550.0, span=-1000.0)

    def test_material_properties_invalid_inputs(self):
        """Test that invalid material properties raise ValueError."""
        with self.assertRaises(ValueError):
            MaterialProperties(f_ck=25.0, f_y=500.0, E_s=0.0)

    def test_factored_loads_invalid_inputs(self):
        """Test that negative factored loads raise ValueError."""
        with self.assertRaises(ValueError):
            FactoredLoads(M_u=-10.0, V_u=50.0)
        with self.assertRaises(ValueError):
            FactoredLoads(M_u=50.0, V_u=-5.0)
        with self.assertRaises(ValueError):
            FactoredLoads(M_u=50.0, V_u=50.0, T_u=-1.0)

    def test_stirrup_details_invalid_inputs(self):
        """Test that invalid stirrup details raise ValueError."""
        with self.assertRaises(ValueError):
            StirrupDetails(num_legs=0, bar_diameter=8.0, spacing=150.0)
        with self.assertRaises(ValueError):
            StirrupDetails(num_legs=2, bar_diameter=-8.0, spacing=150.0)
        with self.assertRaises(ValueError):
            StirrupDetails(num_legs=2, bar_diameter=8.0, spacing=0.0)


if __name__ == "__main__":
    unittest.main()
