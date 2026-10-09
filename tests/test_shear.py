"""
Unit tests for IS 456:2000 Shear Design Module.
"""

import unittest
from structai.core.datatypes import BeamGeometry, MaterialProperties, FactoredLoads, StirrupDetails
from structai.codes.is456.shear import design_shear, interpolate_tau_c
from structai.codes.is456.constants import get_tau_c_max, TABLE_20_TAU_C_MAX


class TestIS456Shear(unittest.TestCase):

    def setUp(self):
        self.geom = BeamGeometry(b=250.0, D=500.0, d=450.0)
        self.materials = MaterialProperties(f_ck=20.0, f_y=415.0, f_yv=415.0)

    def test_tau_c_max_lookup(self):
        """Test maximum permissible shear stress tau_c_max from Table 20."""
        self.assertEqual(get_tau_c_max(15.0), 2.5)
        self.assertEqual(get_tau_c_max(20.0), 2.8)
        self.assertEqual(get_tau_c_max(25.0), 3.1)
        self.assertEqual(get_tau_c_max(30.0), 3.5)
        self.assertEqual(get_tau_c_max(35.0), 3.7)
        self.assertEqual(get_tau_c_max(40.0), 4.0)
        self.assertEqual(get_tau_c_max(50.0), 4.0)  # M40 and above

    def test_table_19_linear_interpolation(self):
        """Test Table 19 design shear strength tau_c interpolation."""
        # Exact table value check: pt = 0.5%, M20 => tau_c = 0.48 N/mm²
        self.assertAlmostEqual(interpolate_tau_c(0.50, 20.0), 0.48, places=3)
        # Exact table value check: pt = 0.75%, M20 => tau_c = 0.56 N/mm²
        self.assertAlmostEqual(interpolate_tau_c(0.75, 20.0), 0.56, places=3)

        # 1D interpolation check: pt = 0.625% (midpoint between 0.50% and 0.75%)
        # Expected tau_c = 0.48 + 0.5 * (0.56 - 0.48) = 0.52 N/mm²
        self.assertAlmostEqual(interpolate_tau_c(0.625, 20.0), 0.52, places=3)

        # Lower bound check: pt = 0.05% (< 0.15%) => tau_c for 0.15% = 0.28 N/mm²
        self.assertAlmostEqual(interpolate_tau_c(0.05, 20.0), 0.28, places=3)

        # Upper bound check: pt = 4.0% (> 3.00%) => tau_c for 3.00% = 0.82 N/mm²
        self.assertAlmostEqual(interpolate_tau_c(4.00, 20.0), 0.82, places=3)

    def test_nominal_shear_stress(self):
        """Test calculation of tau_v = Vu / (b * d)."""
        loads = FactoredLoads(M_u=50.0, V_u=90.0)  # 90 kN = 90,000 N
        # tau_v = 90,000 / (250 * 450) = 0.80 N/mm²
        res = design_shear(self.geom, self.materials, loads, Ast_provided_mm2=708.0)
        self.assertAlmostEqual(res.tau_v_Nmm2, 0.80, places=3)

    def test_shear_design_when_tau_v_less_than_tau_c(self):
        """Test shear design when tau_v <= tau_c (nominal minimum stirrups required)."""
        # Vu = 30 kN => tau_v = 30000 / (250 * 450) = 0.267 N/mm²
        # For pt = 0.63% (Ast = 708 mm²), M20 => tau_c = 0.522 N/mm²
        loads = FactoredLoads(M_u=50.0, V_u=30.0)
        res = design_shear(self.geom, self.materials, loads, Ast_provided_mm2=708.0)

        self.assertFalse(res.shear_reinforcement_required)
        self.assertTrue(res.is_section_safe_in_shear)
        self.assertEqual(res.V_us_kN, 0.0)
        # Check minimum shear rebar spacing for 2-legged 8mm stirrup (Asv = 100.53 mm²):
        # sv_min = 0.87 * 415 * 100.53 / (0.4 * 250) = 362.96 mm
        self.assertAlmostEqual(res.sv_req_min_rebar_mm, 362.96, places=1)
        # Code max spacing limit = min(0.75 * 450, 300) = 300.0 mm
        self.assertAlmostEqual(res.sv_max_code_limit_mm, 300.0, places=1)
        # Governing max spacing = min(300.0, 362.96) = 300.0 mm
        self.assertAlmostEqual(res.governing_max_spacing_mm, 300.0, places=1)

    def test_shear_design_when_tau_v_greater_than_tau_c(self):
        """Test shear design when tau_v > tau_c (stirrups designed for V_us)."""
        # Vu = 100 kN => tau_v = 100000 / (250 * 450) = 0.889 N/mm²
        # Ast = 708 mm² (pt = 0.629%) => tau_c = 0.521 N/mm²
        # V_us = (0.889 - 0.521) * 250 * 450 = 41.34 kN
        loads = FactoredLoads(M_u=80.0, V_u=100.0)
        stirrups = StirrupDetails(num_legs=2, bar_diameter=8.0, spacing=150.0) # Asv = 100.53 mm²
        res = design_shear(self.geom, self.materials, loads, Ast_provided_mm2=708.0, stirrup_details=stirrups)

        self.assertTrue(res.shear_reinforcement_required)
        self.assertTrue(res.is_section_safe_in_shear)
        self.assertGreater(res.V_us_kN, 0.0)
        # Required spacing sv = 0.87 * 415 * 100.53 * 450 / (V_us_N)
        # Expected sv_calc ~ 395 mm (which exceeds governing max spacing 337.5 mm)
        self.assertIsNotNone(res.sv_req_calc_mm)

    def test_shear_stress_exceeds_tau_c_max(self):
        """Test safety failure when tau_v > tau_c_max."""
        # Vu = 350 kN => tau_v = 350000 / (250 * 450) = 3.11 N/mm² > tau_c_max (2.8 N/mm² for M20)
        loads = FactoredLoads(M_u=80.0, V_u=350.0)
        res = design_shear(self.geom, self.materials, loads, Ast_provided_mm2=708.0)

        self.assertFalse(res.is_section_safe_in_shear)

    def test_shear_benchmark_m25_high_shear(self):
        """Test independently verified shear benchmark for M25, Fe500, Vu = 220 kN (b=300, d=550)."""
        geom_b2 = BeamGeometry(b=300.0, D=600.0, d=550.0)
        mat_b2 = MaterialProperties(f_ck=25.0, f_y=500.0, f_yv=500.0)
        loads_b2 = FactoredLoads(M_u=180.0, V_u=220.0)
        stirrups = StirrupDetails(num_legs=2, bar_diameter=8.0, spacing=150.0)

        res = design_shear(geom_b2, mat_b2, loads_b2, Ast_provided_mm2=837.81, stirrup_details=stirrups)

        self.assertAlmostEqual(res.tau_v_Nmm2, 1.333, places=3)
        self.assertAlmostEqual(res.tau_c_Nmm2, 0.4925, places=3)
        self.assertAlmostEqual(res.tau_c_max_Nmm2, 3.10, places=2)
        self.assertAlmostEqual(res.V_us_kN, 138.74, places=2)
        self.assertAlmostEqual(res.sv_req_calc_mm, 173.36, places=2)
        self.assertAlmostEqual(res.sv_req_min_rebar_mm, 364.42, places=2)
        self.assertAlmostEqual(res.sv_max_code_limit_mm, 300.00, places=1)
        self.assertTrue(res.shear_reinforcement_required)
        self.assertTrue(res.is_section_safe_in_shear)

    def test_sub_m15_concrete_raises_exception(self):
        """Test that concrete grades below M15 raise ValueError as per IS 456 Table 19 notes."""
        with self.assertRaises(ValueError) as ctx:
            interpolate_tau_c(0.5, 10.0)
        self.assertIn("below M15", str(ctx.exception))

    def test_table_19_multi_grade_m30_m35_m40_benchmarks(self):
        """Test Table 19 exact & interpolated tau_c values for M30, M35, M40, M50 concrete."""
        # M30 concrete grade benchmarks
        self.assertAlmostEqual(interpolate_tau_c(0.15, 30.0), 0.29, places=3)
        self.assertAlmostEqual(interpolate_tau_c(1.00, 30.0), 0.66, places=3)
        self.assertAlmostEqual(interpolate_tau_c(2.00, 30.0), 0.87, places=3)
        self.assertAlmostEqual(interpolate_tau_c(3.00, 30.0), 0.98, places=3)

        # M35 concrete grade benchmarks
        self.assertAlmostEqual(interpolate_tau_c(0.15, 35.0), 0.29, places=3)
        self.assertAlmostEqual(interpolate_tau_c(1.50, 35.0), 0.79, places=3)
        self.assertAlmostEqual(interpolate_tau_c(3.00, 35.0), 1.04, places=3)

        # M40 concrete grade benchmarks (including interpolation & clamping above 3.00%)
        self.assertAlmostEqual(interpolate_tau_c(0.15, 40.0), 0.30, places=3)
        self.assertAlmostEqual(interpolate_tau_c(3.00, 40.0), 1.09, places=3)
        self.assertAlmostEqual(interpolate_tau_c(3.50, 40.0), 1.09, places=3)  # pt > 3.0% capped to 3.0%

        # M50 concrete grade (capped to M40 per Table 19 Note)
        self.assertAlmostEqual(interpolate_tau_c(3.00, 50.0), 1.09, places=3)


if __name__ == "__main__":
    unittest.main()
