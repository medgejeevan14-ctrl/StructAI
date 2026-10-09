"""
Core datatypes, enums, and data classes for StructAI calculation engines.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class SupportCondition(Enum):
    CANTILEVER = "cantilever"
    SIMPLY_SUPPORTED = "simply_supported"
    CONTINUOUS = "continuous"


class CheckStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass
class CodeCheckResult:
    """Represents the outcome of a specific IS 456 code provision check."""
    check_name: str
    clause: str
    status: CheckStatus
    demand: float
    capacity: float
    unit: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BeamGeometry:
    """
    Rectangular Beam Geometry inputs in SI units (mm).
    
    Attributes:
        b: Width of rectangular beam section (mm)
        D: Overall depth of beam section (mm)
        d: Effective depth of beam section (mm)
        d_prime: Effective cover to compression steel (mm), default 40mm
        span: Clear or effective span of beam (mm)
        support_condition: Support condition type (CANTILEVER, SIMPLY_SUPPORTED, CONTINUOUS)
    """
    b: float
    D: float
    d: float
    d_prime: float = 40.0
    span: Optional[float] = None
    support_condition: SupportCondition = SupportCondition.SIMPLY_SUPPORTED

    def __post_init__(self):
        if self.b <= 0:
            raise ValueError(f"Width b must be positive, got {self.b} mm")
        if self.D <= 0:
            raise ValueError(f"Overall depth D must be positive, got {self.D} mm")
        if self.d <= 0 or self.d >= self.D:
            raise ValueError(f"Effective depth d ({self.d} mm) must be positive and less than overall depth D ({self.D} mm)")
        if self.d_prime < 0 or self.d_prime >= self.D:
            raise ValueError(f"Compression cover d' ({self.d_prime} mm) must be non-negative and less than overall depth D ({self.D} mm)")
        if self.span is not None and self.span <= 0:
            raise ValueError(f"Span must be positive when provided, got {self.span} mm")


@dataclass
class MaterialProperties:
    """
    Material properties for concrete and steel in SI units (N/mm²).
    
    Attributes:
        f_ck: Characteristic compressive strength of concrete at 28 days (N/mm²)
        f_y: Characteristic yield strength of main tension reinforcement (N/mm²)
        f_yv: Characteristic yield strength of shear stirrup reinforcement (N/mm²), defaults to f_y
        E_s: Modulus of elasticity of steel (N/mm²), default 200,000 N/mm² (200 GPa)
        is_hysd: True if main steel is High Yield Strength Deformed (HYSD/TMT), False if plain mild steel
    """
    f_ck: float
    f_y: float
    f_yv: Optional[float] = None
    E_s: float = 200000.0
    is_hysd: bool = True

    def __post_init__(self):
        if self.f_ck <= 0:
            raise ValueError(f"Concrete grade f_ck must be positive, got {self.f_ck} N/mm²")
        if self.f_y <= 0:
            raise ValueError(f"Steel grade f_y must be positive, got {self.f_y} N/mm²")
        if self.f_yv is None:
            self.f_yv = self.f_y
        elif self.f_yv <= 0:
            raise ValueError(f"Stirrup steel grade f_yv must be positive, got {self.f_yv} N/mm²")
        if self.E_s <= 0:
            raise ValueError(f"Modulus of elasticity E_s must be positive, got {self.E_s} N/mm²")


@dataclass
class FactoredLoads:
    """
    Factored design loads acting on the beam section.
    
    Attributes:
        M_u: Factored ultimate bending moment (kNm)
        V_u: Factored ultimate shear force (kN)
        T_u: Factored ultimate torsional moment (kNm), default 0.0 (Phase 1 focus: flexure + shear)
    """
    M_u: float
    V_u: float
    T_u: float = 0.0

    def __post_init__(self):
        if self.M_u < 0:
            raise ValueError(f"Factored bending moment M_u cannot be negative, got {self.M_u} kNm")
        if self.V_u < 0:
            raise ValueError(f"Factored shear force V_u cannot be negative, got {self.V_u} kN")
        if self.T_u < 0:
            raise ValueError(f"Factored torsion T_u cannot be negative, got {self.T_u} kNm")

    @property
    def M_u_Nmm(self) -> float:
        """Converts factored bending moment M_u from kNm to N·mm."""
        return self.M_u * 1e6

    @property
    def V_u_N(self) -> float:
        """Converts factored shear force V_u from kN to N."""
        return self.V_u * 1e3


@dataclass
class StirrupDetails:
    """
    Shear stirrup details provided.
    
    Attributes:
        num_legs: Number of legs of stirrups (e.g. 2, 4)
        bar_diameter: Diameter of stirrup bar (mm)
        spacing: Provided center-to-center spacing of stirrups (mm)
    """
    num_legs: int
    bar_diameter: float
    spacing: float

    def __post_init__(self):
        if self.num_legs <= 0:
            raise ValueError(f"Stirrup number of legs must be positive, got {self.num_legs}")
        if self.bar_diameter <= 0:
            raise ValueError(f"Stirrup bar diameter must be positive, got {self.bar_diameter} mm")
        if self.spacing <= 0:
            raise ValueError(f"Stirrup spacing must be positive, got {self.spacing} mm")

    @property
    def A_sv(self) -> float:
        """Total cross-sectional area of stirrup legs (mm²)."""
        import math
        return self.num_legs * (math.pi / 4.0) * (self.bar_diameter ** 2)


@dataclass
class FlexureDesignResult:
    """Results from IS 456 flexural design calculation."""
    M_u_kNm: float
    M_u_lim_kNm: float
    xu_max_mm: float
    xu_max_d_ratio: float
    xu_mm: float
    is_under_reinforced: bool
    is_doubly_reinforced_required: bool
    Ast_req_mm2: float
    Ast_min_mm2: float
    Ast_max_mm2: float
    pt_req_percent: float
    governing_Ast_mm2: float
    clauses: List[str]
    notes: List[str] = field(default_factory=list)


@dataclass
class ShearDesignResult:
    """Results from IS 456 shear design calculation."""
    V_u_kN: float
    tau_v_Nmm2: float
    tau_c_Nmm2: float
    tau_c_max_Nmm2: float
    pt_provided_percent: float
    shear_reinforcement_required: bool
    is_section_safe_in_shear: bool
    V_us_kN: float
    sv_req_calc_mm: Optional[float]
    sv_req_min_rebar_mm: float
    sv_max_code_limit_mm: float
    governing_max_spacing_mm: float
    clauses: List[str]
    notes: List[str] = field(default_factory=list)


@dataclass
class DevelopmentLengthResult:
    """Detailed breakdown of IS 456 Clause 26.2.1 development length components."""
    tau_bd_plain_Nmm2: float
    hysd_factor: float
    compression_factor: float
    tau_bd_design_Nmm2: float
    sigma_s_Nmm2: float
    bar_diameter_mm: float
    ld_mm: float
    ld_phi_ratio: float
    clause: str = "IS 456:2000 Cl 26.2.1 & Cl 26.2.1.1"


@dataclass
class DeflectionCheckResult:
    """Detailed breakdown of IS 456 Clause 23.2.1 deflection control components."""
    basic_span_depth_ratio: float
    span_10m_correction_factor: float
    fs_Nmm2: float
    pt_provided_percent: float
    pc_provided_percent: float
    modification_factor_F1_tension: float
    modification_factor_F2_compression: float
    modification_factor_F3_flanged_status: CheckStatus
    allowable_span_depth_ratio: float
    actual_span_depth_ratio: Optional[float]
    status: CheckStatus
    clause: str = "IS 456:2000 Cl 23.2.1, Fig 4, Fig 5"


@dataclass
class DetailingCheckResult:
    """Results from IS 456 detailing and code limit checks."""
    development_length: DevelopmentLengthResult
    deflection: DeflectionCheckResult
    development_length_mm: float
    ld_phi_ratio: float
    basic_span_depth_ratio: float
    modification_factor_F1: float
    modification_factor_F2: float
    allowable_span_depth_ratio: float
    actual_span_depth_ratio: Optional[float]
    deflection_check_pass: Optional[bool]
    code_checks: List[CodeCheckResult]
    clauses: List[str]
