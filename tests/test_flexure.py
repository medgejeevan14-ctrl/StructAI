"""
Unit tests for IS 456:2000 Flexural Design Module.
"""

import unittest
from structai.core.datatypes import BeamGeometry, MaterialProperties, FactoredLoads
from structai.codes.is456.flexure import design_flexure_singly_reinforced
from structai.codes.is456.constants import get_xu_max_d_ratio, LIMITING_NEUTRAL_AXIS_RATIO


class TestIS456Flexure(unittest.TestCase):

    def setUp(self):
        # Standard beam geometry: 250mm x 500mm, d = 450mm
        self.geom = BeamGeometry(b=250.0, D=500.0, d=450.0)
        # Standard materials: M20 concrete, Fe415 steel
        self.materials = MaterialProperties(f_ck=20.0, f_y=415.0)

    def test_limiting_neutral_axis_ratios(self):
        """Test xu_max / d ratios for standard steel grades."""
        self.assertEqual(get_xu_max_d_ratio(250.0), 0.53)
        self.assertEqual(get_xu_max_d_ratio(415.0), 0.48)
        self.assertEqual(get_xu_max_d_ratio(500.0), 0.46)
        self.assertEqual(get_xu_max_d_ratio(550.0), 0.44)

    def test_limiting_moment_capacity(self):
        """Test calculation of Mu_lim for M20 and Fe415 beam (b=250, d=450)."""
        loads = FactoredLoads(M_u=50.0, V_u=20.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)
        
        # Hand calculation check:
        # xu_max/d = 0.48 => xu_max = 0.48 * 450 = 216 mm
        # Mu_lim = 0.36 * 0.48 * (1 - 0.42 * 0.48) * 20 * 250 * 450^2 = 139.688 e6 Nmm = 139.69 kNm
        self.assertAlmostEqual(res.xu_max_d_ratio, 0.48, places=3)
        self.assertAlmostEqual(res.xu_max_mm, 216.0, places=2)
        self.assertAlmostEqual(res.M_u_lim_kNm, 139.69, places=2)

    def test_singly_reinforced_ast_calculation(self):
        """Test Ast calculation for applied moment Mu = 100 kNm."""
        loads = FactoredLoads(M_u=100.0, V_u=30.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)

        # Hand calculation check:
        # Ast_req = (0.5 * 20 / 415) * (1 - sqrt(1 - (4.6 * 100e6)/(20 * 250 * 450^2))) * 250 * 450
        # = 708.34 mm²
        self.assertTrue(res.is_under_reinforced)
        self.assertFalse(res.is_doubly_reinforced_required)
        self.assertAlmostEqual(res.Ast_req_mm2, 708.34, places=2)
        self.assertGreater(res.Ast_req_mm2, res.Ast_min_mm2)
        self.assertLess(res.Ast_req_mm2, res.Ast_max_mm2)

    def test_minimum_tension_reinforcement(self):
        """Test Ast_min check when applied moment is small (Mu = 10 kNm)."""
        loads = FactoredLoads(M_u=10.0, V_u=10.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)

        # Ast_min = 0.85 * b * d / f_y = 0.85 * 250 * 450 / 415 = 230.42 mm²
        # Ast_req for 10 kNm = ~62 mm²
        self.assertAlmostEqual(res.Ast_min_mm2, 230.42, places=1)
        self.assertEqual(res.governing_Ast_mm2, res.Ast_min_mm2)

    def test_maximum_tension_reinforcement(self):
        """Test Ast_max limit = 0.04 * b * D."""
        loads = FactoredLoads(M_u=50.0, V_u=10.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)

        # Ast_max = 0.04 * 250 * 500 = 5000 mm²
        self.assertAlmostEqual(res.Ast_max_mm2, 5000.0, places=1)

    def test_doubly_reinforced_trigger(self):
        """Test that applied moment > Mu_lim triggers doubly reinforced flag."""
        # Mu_lim is 139.69 kNm for this section. Apply Mu = 160 kNm.
        loads = FactoredLoads(M_u=160.0, V_u=50.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)

        self.assertTrue(res.is_doubly_reinforced_required)
        self.assertFalse(res.is_under_reinforced)

    def test_flexure_benchmark_fe500_m25(self):
        """Test independently verified benchmark for M25 concrete & Fe500 steel (b=300, d=550)."""
        geom_b2 = BeamGeometry(b=300.0, D=600.0, d=550.0)
        mat_b2 = MaterialProperties(f_ck=25.0, f_y=500.0)
        loads_b2 = FactoredLoads(M_u=180.0, V_u=50.0)
        res = design_flexure_singly_reinforced(geom_b2, mat_b2, loads_b2)

        self.assertAlmostEqual(res.M_u_lim_kNm, 303.12, places=2)
        self.assertAlmostEqual(res.Ast_req_mm2, 837.81, places=2)
        self.assertAlmostEqual(res.xu_mm, 134.98, places=2)
        self.assertAlmostEqual(res.Ast_min_mm2, 280.50, places=2)
        self.assertAlmostEqual(res.Ast_max_mm2, 7200.00, places=2)
        self.assertTrue(res.is_under_reinforced)
        self.assertFalse(res.is_doubly_reinforced_required)

    def test_flexure_exactly_at_limiting_moment(self):
        """Test flexural behavior when applied moment Mu equals Mu_lim (139.68 kNm)."""
        loads = FactoredLoads(M_u=139.68, V_u=50.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)

        self.assertTrue(res.is_under_reinforced)
        self.assertFalse(res.is_doubly_reinforced_required)

    def test_flexure_above_limiting_moment_classification(self):
        """Test flexural classification when Mu exceeds Mu_lim by +1 kNm."""
        loads = FactoredLoads(M_u=140.69, V_u=50.0)
        res = design_flexure_singly_reinforced(self.geom, self.materials, loads)

        self.assertTrue(res.is_doubly_reinforced_required)
        self.assertFalse(res.is_under_reinforced)


if __name__ == "__main__":
    unittest.main()
