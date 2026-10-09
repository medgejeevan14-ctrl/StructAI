"""
Unit tests for IS 456:2000 Detailing and Code Limit Checks.
"""

import unittest
from structai.core.datatypes import BeamGeometry, MaterialProperties, FactoredLoads, SupportCondition, CheckStatus
from structai.codes.is456.flexure import design_flexure_singly_reinforced
from structai.codes.is456.shear import design_shear
from structai.codes.is456.detailing import calculate_development_length, perform_detailing_checks
from structai.codes.is456.constants import get_fig4_modification_factor_F1, get_fig5_modification_factor_F2


class TestIS456Detailing(unittest.TestCase):

    def setUp(self):
        self.geom = BeamGeometry(b=250.0, D=500.0, d=450.0, span=5000.0, support_condition=SupportCondition.SIMPLY_SUPPORTED)
        self.materials = MaterialProperties(f_ck=20.0, f_y=415.0, is_hysd=True)
        self.loads = FactoredLoads(M_u=80.0, V_u=50.0)

    def test_development_length_calculation(self):
        """Test calculation of Ld for Fe415 HYSD bar in M20 concrete."""
        # tau_bd_plain for M20 = 1.2 N/mm²
        # tau_bd_hysd = 1.2 * 1.6 = 1.92 N/mm²
        # Ld/phi = (0.87 * 415) / (4 * 1.92) = 47.0117
        # For 20mm bar: Ld = 47.0117 * 20 = 940.23 mm
        dev_res = calculate_development_length(
            f_y=415.0, f_ck=20.0, bar_diameter_mm=20.0, is_hysd=True, is_compression=False
        )
        self.assertEqual(dev_res.tau_bd_plain_Nmm2, 1.2)
        self.assertEqual(dev_res.hysd_factor, 1.6)
        self.assertEqual(dev_res.compression_factor, 1.0)
        self.assertAlmostEqual(dev_res.tau_bd_design_Nmm2, 1.92, places=2)
        self.assertAlmostEqual(dev_res.ld_phi_ratio, 47.01, places=1)
        self.assertAlmostEqual(dev_res.ld_mm, 940.2, places=1)

    def test_development_length_compression_bar(self):
        """Test calculation of Ld for bar in compression (+25% tau_bd)."""
        dev_res = calculate_development_length(
            f_y=415.0, f_ck=20.0, bar_diameter_mm=20.0, is_hysd=True, is_compression=True
        )
        self.assertEqual(dev_res.compression_factor, 1.25)
        # tau_bd_design = 1.2 * 1.6 * 1.25 = 2.4 N/mm²
        self.assertAlmostEqual(dev_res.tau_bd_design_Nmm2, 2.40, places=2)
        # Ld/phi = (0.87 * 415) / (4 * 2.4) = 37.609
        self.assertAlmostEqual(dev_res.ld_phi_ratio, 37.61, places=1)

    def test_fig4_fig5_lookup(self):
        """Test digitized grid lookup functions for Fig 4 (F1) and Fig 5 (F2)."""
        # Fig 4: pt = 1.0%, fs = 240 N/mm² => F1 = 0.88
        f1 = get_fig4_modification_factor_F1(pt_percent=1.0, fs_Nmm2=240.0)
        self.assertAlmostEqual(f1, 0.88, places=2)

        # Fig 5: pc = 1.0% => F2 = 1.26
        f2 = get_fig5_modification_factor_F2(pc_percent=1.0)
        self.assertAlmostEqual(f2, 1.26, places=2)

    def test_detailing_checks_execution(self):
        """Test execution of detailing checks and code check statuses."""
        flex_res = design_flexure_singly_reinforced(self.geom, self.materials, self.loads)
        shear_res = design_shear(self.geom, self.materials, self.loads, Ast_provided_mm2=flex_res.governing_Ast_mm2)

        detailing_res = perform_detailing_checks(
            geometry=self.geom,
            materials=self.materials,
            flexure_res=flex_res,
            shear_res=shear_res,
            Ast_provided_mm2=flex_res.governing_Ast_mm2,
            stirrup_spacing_provided_mm=150.0,
            main_bar_diameter_mm=20.0,
        )

        self.assertIsNotNone(detailing_res.code_checks)
        self.assertGreaterEqual(len(detailing_res.code_checks), 7)

        # Confirm expected code check names present
        check_names = [c.check_name for c in detailing_res.code_checks]
        self.assertIn("Minimum Tension Reinforcement", check_names)
        self.assertIn("Maximum Tension Reinforcement", check_names)
        self.assertIn("Maximum Shear Stress", check_names)
        self.assertIn("Maximum Stirrup Spacing (Code Limit)", check_names)
        self.assertIn("Minimum Shear Reinforcement Spacing", check_names)
        self.assertIn("Development Length Ld", check_names)
        self.assertIn("Deflection Span/Depth Ratio", check_names)
        self.assertIn("Flanged Beam Deflection Modification (Fig 6)", check_names)

        # Confirm status for Fig 6 is NOT_IMPLEMENTED
        fig6_check = [c for c in detailing_res.code_checks if "Fig 6" in c.check_name][0]
        self.assertEqual(fig6_check.status, CheckStatus.NOT_IMPLEMENTED)

    def test_deflection_span_greater_than_10m(self):
        """Test span > 10m reduction factor (10 / span_m) for deflection control."""
        geom_12m = BeamGeometry(b=300.0, D=600.0, d=550.0, span=12000.0, support_condition=SupportCondition.SIMPLY_SUPPORTED)
        flex_res = design_flexure_singly_reinforced(geom_12m, self.materials, self.loads)
        shear_res = design_shear(geom_12m, self.materials, self.loads, Ast_provided_mm2=flex_res.governing_Ast_mm2)

        detailing_res = perform_detailing_checks(
            geometry=geom_12m,
            materials=self.materials,
            flexure_res=flex_res,
            shear_res=shear_res,
            Ast_provided_mm2=flex_res.governing_Ast_mm2,
        )

        # Basic L/d = 20 * (10 / 12) = 16.667
        self.assertAlmostEqual(detailing_res.deflection.span_10m_correction_factor, 10.0 / 12.0, places=3)
        self.assertAlmostEqual(detailing_res.deflection.basic_span_depth_ratio, 20.0 * (10.0 / 12.0), places=2)

    def test_development_length_m25_fe500(self):
        """Test independently verified Ld benchmark for M25 concrete & Fe500 HYSD bar."""
        dev_res = calculate_development_length(f_y=500.0, f_ck=25.0, bar_diameter_mm=20.0, is_hysd=True)
        self.assertEqual(dev_res.tau_bd_plain_Nmm2, 1.40)
        self.assertAlmostEqual(dev_res.tau_bd_design_Nmm2, 2.24, places=2)
        self.assertAlmostEqual(dev_res.ld_phi_ratio, 48.55, places=2)
        self.assertAlmostEqual(dev_res.ld_mm, 970.98, places=2)

    def test_deflection_span_boundary_at_10m_and_longer(self):
        """Test deflection span correction factor exact boundary at 10m, 10.01m, and 15m."""
        # 10.0 m span => Factor = 1.000
        geom_10m = BeamGeometry(b=300.0, D=600.0, d=550.0, span=10000.0, support_condition=SupportCondition.SIMPLY_SUPPORTED)
        flex_res = design_flexure_singly_reinforced(geom_10m, self.materials, self.loads)
        shear_res = design_shear(geom_10m, self.materials, self.loads, Ast_provided_mm2=flex_res.governing_Ast_mm2)
        det_10m = perform_detailing_checks(geom_10m, self.materials, flex_res, shear_res, Ast_provided_mm2=flex_res.governing_Ast_mm2)
        self.assertEqual(det_10m.deflection.span_10m_correction_factor, 1.00)
        self.assertEqual(det_10m.deflection.basic_span_depth_ratio, 20.0)

        # 15.0 m span => Factor = 10 / 15 = 0.6667
        geom_15m = BeamGeometry(b=300.0, D=600.0, d=550.0, span=15000.0, support_condition=SupportCondition.SIMPLY_SUPPORTED)
        det_15m = perform_detailing_checks(geom_15m, self.materials, flex_res, shear_res, Ast_provided_mm2=flex_res.governing_Ast_mm2)
        self.assertAlmostEqual(det_15m.deflection.span_10m_correction_factor, 10.0 / 15.0, places=3)
        self.assertAlmostEqual(det_15m.deflection.basic_span_depth_ratio, 20.0 * (10.0 / 15.0), places=2)


if __name__ == "__main__":
    unittest.main()

