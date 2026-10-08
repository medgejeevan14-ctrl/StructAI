# StructAI

A modular Python framework for structural engineering design automation and IS 456:2000 code compliance checks.

---

## 1. Project Description

**StructAI** is an open-source, modular Python framework developed to automate reinforced concrete structural design calculations and code compliance audits per **IS 456:2000** (Indian Standard Code of Practice for Plain and Reinforced Concrete).

It provides a transparent domain engine with full mathematical traceability, explicit clause references, and step-by-step intermediate calculation logging.

---

## 2. Implemented Functionality & IS 456:2000 Modules

StructAI v0.1.0 includes the following core engineering design modules:

1. **Flexural Design (Annex G & Clause 38.1):**
   - Limiting neutral axis depth ratio ($x_{u,max}/d$) for Fe 250, Fe 415, Fe 500, and Fe 550 steel grades.
   - Limiting moment of resistance ($M_{u,lim}$) calculation for rectangular sections.
   - Exact quadratic solution for required tension reinforcement ($A_{st,req}$) for singly reinforced sections.
   - Code tension steel checks: Minimum tension steel ($A_{st,min}$, Clause 26.5.1.1 a) and Maximum tension steel ($A_{st,max}$, Clause 26.5.1.1 b).

2. **Shear Design (Clause 40 & Clause 26.5.1):**
   - Nominal shear stress ($\tau_v = V_u / b d$, Clause 40.1).
   - Maximum permissible shear stress ($\tau_{c,max}$, Clause 40.2.3 Table 20).
   - Concrete design shear strength ($\tau_c$, Clause 40.2.1 Table 19) via exact 2D bilinear interpolation, with explicit error handling for concrete grades below M15.
   - Shear stirrup design for net shear force ($V_{us} = V_u - \tau_c b d$, Clause 40.4).
   - Minimum shear reinforcement limit ($s_{v,min}$, Clause 26.5.1.6) and maximum stirrup spacing limit ($\min(0.75 d, 300\text{ mm})$, Clause 26.5.1.5).

3. **Development Length (Clause 26.2.1 & Clause 26.2.1.1):**
   - Base design bond stress ($\tau_{bd,plain}$) lookup for plain bars in tension.
   - $+60\%$ adjustment factor for deformed/HYSD bars.
   - $+25\%$ adjustment factor for bars in compression.
   - Computation of design bond stress ($\tau_{bd,design}$), development length ratio ($L_d/\phi$), and development length ($L_d$) in mm.

4. **Deflection Control & Serviceability (Clause 23.2.1):**
   - Basic span-to-effective-depth ratios ($(L/d)_{basic}$): Cantilever ($7$), Simply Supported ($20$), Continuous ($26$).
   - Span $> 10\text{ m}$ correction factor ($10 / \text{span in meters}$).
   - Tension reinforcement modification factor ($F_1$ / $K_t$) via digitized 2D grid bilinear interpolation of **IS 456 Fig. 4**.
   - Compression reinforcement modification factor ($F_2$ / $K_c$) via digitized 1D grid interpolation of **IS 456 Fig. 5**.

5. **Code Audit & Traceability:**
   - Unified engine ([`IS456BeamDesignEngine`](file:///c:/JEEVAN/StructAI/structai/codes/is456/beam.py)) orchestrating flexure, shear, and detailing.
   - Every code check outputs check name, clause reference, demand/input, capacity/limit, unit, and status (`PASS`, `FAIL`, `WARNING`, `NOT_IMPLEMENTED`).

---

## 3. Verification & Test Status

- **Automated Unit Test Suite:** 18 out of 18 tests passing cleanly (`python -m unittest discover -s tests`).
- **Engineering Verification Report:** Complete step-by-step hand calculations documented in [`examples/verification_report.md`](file:///c:/JEEVAN/StructAI/examples/verification_report.md).
- **Sample Demonstration:** Executable verification script in [`examples/sample_beam_calc.py`](file:///c:/JEEVAN/StructAI/examples/sample_beam_calc.py).

---

## 4. Known Limitations (Phase 1 Scope)

- **Doubly Reinforced Flexure:** Doubly reinforced design ($M_u > M_{u,lim}$) flags a requirement warning and is postponed to Phase 2.
- **Flanged Sections:** T-Beam / L-Beam flexural design and Fig. 6 deflection factor $F_3$ are currently marked as `NOT_IMPLEMENTED`.
- **Torsion:** Combined shear, bending, and torsion (Clause 41) is not included in Phase 1.
- **Columns & Slabs:** Compression members (Clause 39) and slabs (Clause 24) are planned for future releases.

---

## 5. Engineering Disclaimer

> [!CAUTION]
> **IMPORTANT DISCLAIMER:**
> **StructAI is an automated calculation utility intended for educational, research, and technical workflow automation purposes.**
> **StructAI is NOT a substitute for independent engineering verification, professional judgment, or official design review by a qualified Licensed Professional Structural Engineer.**
> **Always verify critical structural calculations independently before construction or professional execution.**

---

## 6. Installation & Usage

```bash
# Run automated test suite
python -m unittest discover -s tests

# Run sample beam calculation
python examples/sample_beam_calc.py
```
