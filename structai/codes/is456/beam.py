"""
IS 456:2000 Integrated Beam Design Engine.

Orchestrates flexure, shear, and detailing analysis into a single, cohesive
calculation workflow.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from structai.core.datatypes import (
    BeamGeometry,
    MaterialProperties,
    FactoredLoads,
    StirrupDetails,
    FlexureDesignResult,
    ShearDesignResult,
    DetailingCheckResult,
    CheckStatus,
)
from structai.codes.is456.flexure import design_flexure_singly_reinforced
from structai.codes.is456.shear import design_shear
from structai.codes.is456.detailing import perform_detailing_checks


@dataclass(frozen=True)
class BeamDesignSummary:
    """Comprehensive summary of IS 456 beam design analysis."""
    geometry: BeamGeometry
    materials: MaterialProperties
    loads: FactoredLoads
    flexure: FlexureDesignResult
    shear: ShearDesignResult
    detailing: DetailingCheckResult
    is_overall_pass: bool
    summary_notes: List[str] = field(default_factory=list)


class IS456BeamDesignEngine:
    """
    Primary design engine for IS 456:2000 compliant reinforced concrete rectangular beam design.
    """

    def __init__(
        self,
        geometry: BeamGeometry,
        materials: MaterialProperties,
        loads: FactoredLoads,
        stirrup_details: Optional[StirrupDetails] = None,
        Ast_provided_mm2: Optional[float] = None,
        Asc_provided_mm2: float = 0.0,
        stirrup_spacing_provided_mm: Optional[float] = None,
        main_bar_diameter_mm: float = 20.0,
    ):
        self.geometry = geometry
        self.materials = materials
        self.loads = loads
        self.stirrup_details = stirrup_details
        self.Ast_provided_mm2 = Ast_provided_mm2
        self.Asc_provided_mm2 = Asc_provided_mm2
        self.stirrup_spacing_provided_mm = stirrup_spacing_provided_mm
        self.main_bar_diameter_mm = main_bar_diameter_mm

    def run_design(self) -> BeamDesignSummary:
        """
        Executes full IS 456:2000 beam design workflow:
        1. Singly reinforced flexural design (Annex G)
        2. Shear design & Table 19 interpolation (Clause 40)
        3. Detailing and code compliance checks (Clauses 23, 26, 40)

        Returns:
            BeamDesignSummary containing step-by-step results and overall pass/fail status.
        """
        summary_notes: List[str] = []

        # Step 1: Flexure Design
        flexure_res = design_flexure_singly_reinforced(
            geometry=self.geometry,
            materials=self.materials,
            loads=self.loads,
        )

        if flexure_res.is_doubly_reinforced_required:
            summary_notes.append("WARNING: Section requires doubly reinforced design (Mu > Mu_lim).")

        # Ast provided for shear lookup and detailing checks
        ast_for_shear = (
            self.Ast_provided_mm2
            if self.Ast_provided_mm2 is not None
            else flexure_res.governing_Ast_mm2
        )

        # Step 2: Shear Design
        shear_res = design_shear(
            geometry=self.geometry,
            materials=self.materials,
            loads=self.loads,
            Ast_provided_mm2=ast_for_shear,
            stirrup_details=self.stirrup_details,
        )

        if not shear_res.is_section_safe_in_shear:
            summary_notes.append("CRITICAL: Section fails maximum shear stress check (tau_v > tau_c_max).")

        # Step 3: Detailing & Code Checks
        detailing_res = perform_detailing_checks(
            geometry=self.geometry,
            materials=self.materials,
            flexure_res=flexure_res,
            shear_res=shear_res,
            Ast_provided_mm2=self.Ast_provided_mm2,
            Asc_provided_mm2=self.Asc_provided_mm2,
            stirrup_spacing_provided_mm=self.stirrup_spacing_provided_mm,
            main_bar_diameter_mm=self.main_bar_diameter_mm,
        )

        # Determine overall pass status
        all_checks_pass = True
        for check in detailing_res.code_checks:
            if check.status == CheckStatus.FAIL:
                all_checks_pass = False
                summary_notes.append(f"CHECK FAILED: {check.check_name} ({check.clause})")
            elif check.status == CheckStatus.NOT_IMPLEMENTED:
                summary_notes.append(f"SCOPE LIMITATION: {check.check_name} ({check.clause}) is NOT_IMPLEMENTED.")

        if flexure_res.is_doubly_reinforced_required:
            all_checks_pass = False

        return BeamDesignSummary(
            geometry=self.geometry,
            materials=self.materials,
            loads=self.loads,
            flexure=flexure_res,
            shear=shear_res,
            detailing=detailing_res,
            is_overall_pass=all_checks_pass,
            summary_notes=summary_notes,
        )
