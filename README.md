# StructAI

**StructAI** is a Python engineering framework and Streamlit application for automated structural concrete design per **IS 456:2000**, paired with Anthropic Claude for AI-powered design explanations.

---

## 📌 Overview & Engineering Safety Boundary

Traditional structural engineering software often operates as a black box without clear audit trails, while raw generative AI models can hallucinate engineering formulas and code safety checks.

StructAI addresses this with a strict **Deterministic Engine / AI Safety Boundary**:
- **Deterministic Python Engine**: Calculates all flexural, shear, development length, and serviceability deflection checks strictly according to IS 456:2000 rules.
- **Claude Explanation Layer**: Reads verified engine outputs to generate natural-language technical rationales and code explanations without altering any numerical results.

---

## 📁 Repository Structure

```text
StructAI/
├── structai/                 # Engineering engine & AI assistance package
│   ├── core/                 # Datatypes & validation schemas
│   ├── codes/is456/          # IS 456:2000 beam design modules
│   └── ai/                   # Claude API integration & prompt engine
├── app.py                    # Streamlit interactive web dashboard
├── tests/                    # 52 automated unit & integration tests
└── requirements.txt          # Python dependencies
```

---

## ⚙️ Core Implemented Capabilities (IS 456:2000)

- **Flexural Design**: Limiting moment of resistance ($M_{u,lim}$), singly reinforced tension steel ($A_{st}$), and min/max steel checks (Annex G & Cl 38.1).
- **Shear Design**: Nominal shear stress ($\tau_v$), concrete shear strength ($\tau_c$, Table 19 2D interpolation), max shear limit ($\tau_{c,max}$, Table 20), and stirrup spacing ($s_v$, Cl 40 & Cl 26.5.1).
- **Detailing & Serviceability**: Tension bond development length ($L_d$, Cl 26.2.1) and span-to-effective-depth ratio deflection checks ($L/d$, Fig. 4/5 interpolation, Cl 23.2.1).
- **Interactive UI & Audit**: Streamlit dashboard (`app.py`) providing interactive design inputs, clause audit tables (`PASS`/`FAIL`), and optional Claude explanations.

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/medgejeevan14-ctrl/StructAI.git
cd StructAI
pip install -r requirements.txt
```

### 2. Run Application

**macOS / Linux (Bash):**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"  # Optional
streamlit run app.py
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"  # Optional
streamlit run app.py
```

### 3. Run Tests
```bash
python -m unittest discover -s tests
```
*Current test suite: **52 unit and integration tests** passing.*

---

## ⚠️ Scope & Engineering Limitations

- **Current Scope**: Rectangular singly reinforced RC beams ($M_u \le M_{u,lim}$).
- **Unsupported Features**: Doubly reinforced sections ($M_u > M_{u,lim}$), flanged sections (T/L-beams), and combined torsion are currently marked as `NOT_IMPLEMENTED`.
- **Engineering Use**: StructAI is an automated design utility. All structural calculations must be verified by a Licensed Professional Structural Engineer.

---

## 🗺️ Roadmap

- [x] **Phase 1–4**: Singly reinforced beam engine, Streamlit UI, Claude AI explanation assistant, and 52-test validation suite.
- [ ] **Phase 5**: Doubly reinforced beams and flanged sections (T-beams / L-beams).
- [ ] **Phase 6**: Combined shear, bending, and torsion per Clause 41.
- [ ] **Phase 7**: Additional element design (Columns, Slabs, Footings).
- [ ] **Phase 8**: ETABS / STAAD structural analysis output import.

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
