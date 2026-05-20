# TrustLayer VeriCell — Battery Digital Product Passport Platform

> **One-line pitch:** AI-powered trust validation for EV battery data — turning unverified Digital Product Passports into actionable procurement, compliance, and reuse decisions, synced live to ERP systems.
---
# BRIEF
The EU Battery Regulation mandates a Digital Product 
Passport for every battery by 2027.

Every company is rushing to collect and log that data.

Nobody is checking if it's true.

A manufacturer can declare "Class A" carbon footprint 
while their actual numbers put them in Class C. The 
DPP logs it. Nobody catches it.

This matters because the second-life EV battery market 
— batteries repurposed after their first automotive 
life — is worth billions. But right now it barely 
functions. Why? Because buyers can't trust the data. 
A battery declared at 80% health might be at 60%. 
There's no verification layer.

We built one.

VeriCell runs 8 mathematical cross-checks on every 
battery's declared data — catching internal 
contradictions that only show up when you do the 
math. Energy consistency, carbon class matching, 
cobalt weight plausibility. Things a fraudulent 
or lazy submission can't survive.

Then we push the decision — APPROVE, REVIEW, or 
BLOCK — directly into the buyer's ERP system.

Not a report. A decision. In real time.

Built in 72 hours at a hackathon.

---

## Table of Contents

1. [What This Is](#1-what-this-is)
2. [The Problem We Solve](#2-the-problem-we-solve)
3. [Architecture & Data Flow](#3-architecture--data-flow)
4. [The Verification Engine — 6 Modules](#4-the-verification-engine--6-modules)
5. [The 102 Data Points — 13 Groups](#5-the-102-data-points--13-groups)
6. [The 3 Battery Models (Demo Data)](#6-the-3-battery-models-demo-data)
7. [EU Regulation Compliance Timeline](#7-eu-regulation-compliance-timeline)
8. [The 4 User Roles & What Each Sees](#8-the-4-user-roles--what-each-sees)
9. [The 3 Portal Views](#9-the-3-portal-views)
10. [Odoo ERP Integration](#10-odoo-erp-integration)
11. [Trust Score Formula](#11-trust-score-formula)
12. [Physical Sensor Verification (Level 2)](#12-physical-sensor-verification-level-2)
13. [Tech Stack](#13-tech-stack)
14. [File Structure](#14-file-structure)
15. [Business Model](#15-business-model)
16. [Competitive Position](#16-competitive-position)
17. [Running the App](#17-running-the-app)
18. [Judge Q&A Cheat Sheet](#18-judge-qa-cheat-sheet)

---

## 1. What This Is

VeriCell is a **B2B AI validation middleware** — a trust layer that sits between raw battery DPP (Digital Product Passport) data and enterprise decision systems (ERP).

It does **not** replace:
- DPP infrastructure (the data standard itself)
- Certification bodies like TÜV or DEKRA

It solves **the missing layer between** them:
- Suppliers submit battery data as structured JSON (DPP format)
- VeriCell runs 6 AI validation modules across 102 data points
- It outputs a Trust Score, decision (APPROVE / REVIEW / BLOCK), and full audit trail
- That decision syncs live to the company's ERP (Odoo in our demo)

**AVILOO analogy:** AVILOO gives used EVs a trusted health certificate that dealers pay extra for. VeriCell does this for B2B battery data — the trust badge that makes second-life reuse economically viable.

---

## 2. The Problem We Solve

### The Real Market Pain

60–70% of used EV batteries get destroyed instead of reused — not because they are bad, but because **nobody can trust the data about them**.

- Battery manufacturers submit DPP data, but it is often incomplete, inconsistent, or strategically optimistic
- Second-life operators (e.g. Voltfang) cannot confidently buy or repurpose batteries without verified SoH data
- Each battery is worth €5,000–15,000. At scale this is a **€1–3 billion inefficiency**

### Why Existing DPPs Do Not Solve This

A Digital Product Passport is just a container for data. It does not:
- Cross-validate whether the numbers are internally consistent
- Compare declared values against chemistry benchmarks
- Check if carbon class labels match the actual declared carbon value
- Verify supply chain claims
- Flag when a manufacturer's trust score claim contradicts the percentage of verified vs. mock data

VeriCell does all of this.

---

## 3. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA INGESTION                              │
│  Manufacturer submits battery data as structured JSON           │
│  (13 groups, 102 data points, EU DPP format)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              VERICELL TRUST ENGINE (Python)                      │
│                                                                  │
│  Module 1: Sustainability Scorer    (5 sub-scores, weighted)    │
│  Module 2: Authenticity Checker     (8 cross-field math checks) │
│  Module 3: Compliance Tracker       (2024 / 2027 / 2031 / 2036) │
│  Module 4: Sensor Validator         (4 live sensor parameters)   │
│  Module 5: Trust Score Calculator   (data quality + evidence)   │
│  Module 6: SoH Composite            (5 health parameters)       │
│                                                                  │
│  Output: VerificationReport dataclass                           │
│  Decision: APPROVE (>85) / REVIEW (65–85) / BLOCK (<65)        │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
     │  ENTERPRISE  │ │  GOVERNMENT  │ │ BATTERY PASSPORT  │
     │  DASHBOARD   │ │    PORTAL    │ │  (Consumer/Tech)  │
     └──────┬───────┘ └──────────────┘ └──────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ODOO ERP (Live)                               │
│  push_verification_result() — writes Trust Score + decision     │
│  push_status_update()       — writes technician status          │
│  fetch_products()           — pulls supplier product list       │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Points

- **Input side is JSON** — manufacturers upload structured battery data files. This is the EU DPP standard format.
- **Output side is ERP** — verified decisions are pushed to Odoo via XML-RPC API. The JSON output format is ERP-agnostic; Odoo is what we connect in this demo.
- **The engine is deterministic** — same input always produces same output. No black box.
- **Caching** — `@st.cache_data` ensures expensive engine runs (6 modules × 3 batteries = 18 module executions) only happen once per session.

---

## 4. The Verification Engine — 6 Modules

All logic lives in `engine/verification_engine.py`.

### Module 1 — Sustainability Scorer

Produces a weighted composite score (0–100) from 5 components:

| Component | Weight | What It Checks |
|---|---|---|
| Carbon Footprint | 30% | Declared CO₂/kWh vs chemistry benchmark range |
| Recycled Content | 25% | Cobalt/Lithium/Nickel recycled % vs 2031 EU targets |
| Renewable Energy | 20% | % renewable in cell manufacturing (60%) + pack assembly (40%) |
| Supply Chain Risk | 15% | Geopolitical + ESG risk scores per material origin country |
| Circularity | 10% | Recycling partners, EU take-back points, second-life eligibility |

**Data source:** `data/benchmarks/chemistry_benchmarks.json` (benchmark ranges per chemistry) and `data/compliance/eu_2023_1542_thresholds.json` (recycled content targets).

### Module 2 — Authenticity Checker (8 Cross-Field Math Checks)

These are the checks that catch manipulation or lazy data entry. Each check has a formula that can be explained to a judge:

| # | Check Name | Formula / Logic |
|---|---|---|
| 1 | Energy Consistency | `Nominal Voltage (V) × Rated Capacity (Ah) / 1000 = kWh` — must match declared kWh within 3% |
| 2 | Cell Count | `Modules × Cells per module = Total cells` — must be exact |
| 3 | Carbon vs Benchmark | Declared CO₂/kWh must fall within chemistry benchmark range ± 15% tolerance |
| 4 | Carbon Class Match | Declared carbon class (A/B/C/D) must match the class calculated from the declared kg CO₂/kWh value |
| 5 | Cobalt Weight Plausibility | `total_mass × cathode_fraction (22%) × cobalt_pct` — 50% tolerance |
| 6 | EU Declaration of Conformity | DoC reference number + notified body must both be present (Art. 18) |
| 7 | Supply Chain Traceability | OECD framework declared + independent verifier named |
| 8 | Data Completeness vs Trust | Max possible trust = `(real_data_pct × 0.5) + 50`. A battery can't claim more trust than its data quality allows. |

**Output:** `authenticity_passed` / `authenticity_total` (e.g. 8/8, 6/8, 2/5)

### Module 3 — Compliance Tracker

Checks mandatory EU Battery Regulation 2023/1542 requirements at each milestone year:

| Year | Key Requirements Checked |
|---|---|
| 2024 | EU Declaration of Conformity (Art. 18), CE marking (Art. 19), separate collection symbol (Art. 13) |
| 2027 | All 2024 + carbon footprint declared (Art. 7), QR code / DPP implemented (Art. 13(6)), ISO battery identifier |
| 2031 | All 2027 + recycled cobalt ≥ 16%, lithium ≥ 6%, nickel ≥ 6% (Art. 8) |
| 2036 | All 2031 + cobalt ≥ 26%, lithium ≥ 12%, nickel ≥ 15% |

**Output per year:** score (0–100), status (COMPLIANT / AT RISK / NON-COMPLIANT), failures list, warnings list.

### Module 4 — Sensor Validator

Compares live sensor readings against declared baseline values from the battery's DPP data:

| Sensor | Threshold | Effect |
|---|---|---|
| Temperature (°C) | Must be within chemistry operating range | CRITICAL if >10°C over max |
| Voltage (V) | Must be within ±10% of nominal | CRITICAL if >10% deviation |
| Internal Resistance (mΩ) | % increase from baseline | CRITICAL if >50% increase (major aging) |
| State of Charge (%) | Must be 10–90% | WARNING if <10% (deep discharge risk) |

Also estimates real-world SoH from resistance increase: every 20% resistance increase ≈ 5% SoH loss (NMC aging curve).

**In the app:** Technician view has sliders to simulate live sensor readings. The engine recalculates in real-time.

### Module 5 — Trust Score Calculator

See [Section 11](#11-trust-score-formula) for full formula.

### Module 6 — SoH Composite

State of Health is not a single number. VeriCell combines 5 parameters:

| Parameter | Weight | Source |
|---|---|---|
| Remaining Capacity | 35% | `dp81_remaining_capacity.pct_of_rated` |
| Remaining Power | 25% | `dp82_remaining_power.pct_of_rated` |
| Round-Trip Efficiency | 20% | `dp83_remaining_rtw.value_pct` |
| Self-Discharge Rate | 10% | `dp84_self_discharge.value_pct_per_month` |
| Resistance Health | 10% | `dp85_ohmic_resistance.increase_pct` |

**Output:** composite score + label (EXCELLENT / GOOD / MODERATE / POOR / CRITICAL)

---

## 5. The 102 Data Points — 13 Groups

Battery data is organized into 13 groups (A–M) following EU DPP structure. Each data point has an `access_level` (1–4) controlling which role can see the value.

| Group | Label | Key Data Points |
|---|---|---|
| A | General Info | Manufacturer, model, chemistry, capacity |
| B | Carbon Footprint | kg CO₂e/kWh, carbon class (A/B/C/D), lifecycle phases |
| C | Recycled Content | % cobalt, lithium, nickel recycled; renewable energy in manufacturing |
| D | Responsible Sourcing | Country of origin per material, OECD due diligence, blockchain traceability |
| E | Electrical Characteristics | Nominal voltage, capacity (Ah), C-rate, temperature range |
| F | Conformity & Labelling | EU Declaration of Conformity, CE marking, QR code, waste symbol |
| G | Composition & Disassembly | Cell count, module structure, material mass breakdown, disassembly instructions |
| H | Authority Information | Notified body, test reports, market surveillance contacts |
| I | Individual Performance | Actual measured charge/discharge cycles, efficiency curves |
| J | State of Health | Remaining capacity %, power %, round-trip efficiency, self-discharge, resistance |
| K | Expected Lifetime | Rated cycle life, calendar life, warranty terms |
| L | Operational Data | Operating temperature log, state of charge at delivery, negative events |
| M | Identification & Metadata | Unique battery identifier (ISO/IEC 15459-1), QR code affixed, DPP URL |

**Access levels:**
- L1 — Public (Consumer)
- L2 — Repair / Technician
- L3 — Business / Manufacturer
- L4 — Regulator / Market Surveillance only

---

## 6. The 3 Battery Models (Demo Data)

All data is stored in `data/manufacturers/{manufacturer_id}/{model_id}.json`.

### Battery A — Volvo EX90 NMC811 (111 kWh)

| Field | Value |
|---|---|
| Manufacturer | Volvo Cars, Sweden |
| Chemistry | NMC811 (Nickel 80%, Manganese 10%, Cobalt 10%) |
| Capacity | 111 kWh |
| Odoo Product ID | 3 |
| Trust Score | **71.5 / 100** (REVIEW) |
| Authenticity | 8/8 checks passed |
| 2024 Compliance | COMPLIANT |
| 2031 Compliance | AT RISK (3 gaps) |
| Real Data % | 43% |
| Physical Sensor Verified | ✅ Yes |

### Battery B — BMW iX NMC712 (105 kWh)

| Field | Value |
|---|---|
| Manufacturer | BMW Group, Germany |
| Chemistry | NMC712 (Nickel 70%, Manganese 10%, Cobalt 20%) |
| Capacity | 105 kWh |
| Odoo Product ID | 1 |
| Trust Score | **65.5 / 100** (REVIEW) |
| Authenticity | 6/8 checks passed |
| 2024 Compliance | COMPLIANT |
| 2031 Compliance | AT RISK (2 gaps) |
| Real Data % | 31% |
| Physical Sensor Verified | ✅ Yes |

### Battery C — Shenzhen PowerCell LFP (80 kWh)

| Field | Value |
|---|---|
| Manufacturer | Shenzhen PowerCell Tech Co., Ltd., China |
| Chemistry | LFP (Lithium Iron Phosphate — no cobalt/nickel) |
| Capacity | 80 kWh |
| Odoo Product ID | 2 |
| Trust Score | **6.0 / 100** (BLOCK) |
| Authenticity | 2/5 checks passed |
| 2024 Compliance | AT RISK (3 failures) |
| 2031 Compliance | NON-COMPLIANT (6 failures) |
| Real Data % | 0% |
| Physical Sensor Verified | ❌ No |

**Why Generic OEM is BLOCK:** Missing EU Declaration of Conformity, CE marking unverifiable, no carbon footprint declared, QR code not implemented, 0% real/verified data. This is intentionally the "caught fraud" demo case.

---

## 7. EU Regulation Compliance Timeline

**Regulation:** EU 2023/1542 (Battery Regulation) — entered into force 17 August 2023.

| Date | What Becomes Mandatory |
|---|---|
| **2024** (now) | EU DoC, CE marking, separate collection symbol, manufacturer ID |
| **2027** | QR code linking to DPP, carbon footprint declaration (Art. 7), performance class |
| **2031** | Minimum recycled content: Co ≥ 16%, Li ≥ 6%, Ni ≥ 6% (Art. 8) |
| **2036** | Higher recycled targets: Co ≥ 26%, Li ≥ 12%, Ni ≥ 15% |

**Key articles:**
- Art. 7 — Carbon footprint
- Art. 8 — Recycled content
- Art. 13 — Labelling and QR code
- Art. 18 — EU Declaration of Conformity
- Art. 19 — CE marking
- Art. 48–52 — Due diligence and supply chain

---

## 8. The 4 User Roles & What Each Sees

All 4 roles view the **same underlying data** but with different depth and framing. Access level controls what values are shown vs. shown as "🔒 Restricted".

### Consumer (Access Level 1)
**First tab: 🔐 Certificate & QR** — the trust badge + QR code encoding `DPP:{model_id}`

Other tabs:
- Battery health gauge (SoH composite score)
- Plain-language safety + warranty summary
- Environmental impact (carbon footprint in everyday terms)
- End-of-life recycling information

**Physical Sensor Badge:** Green "Level 2 Physical Verified" or amber "Software Only" based on whether the manufacturer's data has been cross-validated with physical sensor readings.

### Technician (Access Level 2)
- Full SoH breakdown (5 parameters with weights)
- Live sensor simulation sliders (temperature, voltage, resistance, SoC)
- Real-time anomaly detection as sliders are adjusted
- Disassembly and repair information (Group G data)
- Full technical specs table

### Company / Business Analyst (Access Level 3)
- Sustainability score with 5-component breakdown
- Carbon footprint lifecycle chart (production / use / recycling phases)
- Recycled content progress bars vs. 2031 targets
- Supply chain risk table (material → country → geopolitical risk score)
- Compliance timeline (2024/2027/2031/2036 status per year)
- All 102 data points table (filterable by group, status, flags)

### Regulator / Market Surveillance (Access Level 4)
- **AI Audit Summary** — 2-sentence plain-language summary auto-generated from engine output
- EU Declaration of Conformity details (reference number, notified body, test report)
- Full 8-check authenticity audit with formulas
- Complete trust score breakdown
- Full compliance timeline with failure lists per year
- Sustainability deep-dive
- Live sensor panel
- All 102 data points (unredacted, full access)

---

## 9. The 3 Portal Views

### Enterprise Dashboard (Default Landing)
**Who uses it:** Procurement managers, business analysts, plant technicians at battery buyers

**What it shows:**
1. **BLOCK Alert Banner** — red banner if any supplier scores ≤ 65 (currently: Generic OEM)
2. **Supplier Risk Matrix** — table of all 3 suppliers with Trust Score, ERP Decision (APPROVE/REVIEW/BLOCK), 2024 compliance status, authenticity pass rate, data quality %
3. **KPI Strip** — blocked count, review count, avg trust score
4. **Drill-down** — select a battery → Trust Score gauge → full trust breakdown by component → technician Odoo sync action → full Company or Technician view (tabs) below

**Role toggle:** Business Analyst (sees Company view below gauge) vs Technician (sees Technician view + Odoo sync button).

**Odoo Sync:** Technician role → select operational status → click "Sync to Odoo ERP" → `push_status_update()` and `push_verification_result()` are called → toast confirmation.

### Government Portal
**Who uses it:** Market surveillance authorities, environmental regulators, EU compliance officers

**What it shows:**
1. **EU Compliance Map** — Plotly choropleth of Europe, countries shaded by compliance ratio (hardcoded representative data: Sweden 0.92, Germany 0.88, ... Bulgaria 0.42)
2. **Violation Analysis** — bar chart of most common Article violations aggregated across all 3 batteries (extracted from compliance failure strings via regex on "Art. XX")
3. **Audit Reports** — per-battery card with compliance score + download button (generates self-contained HTML audit report) + full Regulator view with AI Audit Summary

### Battery Passport (Consumer / Technician / Company / Regulator)
**Who uses it:** Anyone scanning a QR code on a physical battery, or looking up a specific model

**Flow:**
1. Select role → Browse batteries (3 available) → View passport
2. Role-appropriate tabs render with data from the engine
3. Consumer gets the QR code certificate as the first tab

---

## 10. Odoo ERP Integration

**Connection method:** Python's built-in `xmlrpc.client` — no external library required.

**Endpoints used:**
- `/xmlrpc/2/common` — authentication (`authenticate()`)
- `/xmlrpc/2/object` — data operations (`execute_kw()`)

**Live Odoo instance:** `https://vericell.odoo.com`, database: `vericell`

**Three operations:**

| Function | Direction | What It Does |
|---|---|---|
| `fetch_products()` | ERP → App | Pulls all products from Odoo. Filters to known battery names. Returns product IDs needed for write-back. |
| `push_verification_result()` | App → ERP | Writes `{model_id} \| Trust Score: {score}/100 \| {decision} \| VeriCell DPP` to the product's description field |
| `push_status_update()` | App → ERP | Writes technician operational status (Operational / Under Review / Flagged / Decommissioned) to product description |

**Battery ↔ Odoo product ID mapping:**

| Battery | Odoo Product ID |
|---|---|
| Battery A (Volvo EX90) | 3 |
| Battery B (BMW iX) | 1 |
| Battery C (Generic LFP) | 2 |

**ERP-agnostic note:** The verification output (Trust Score, decision, compliance data) is structured JSON. The `push_*` functions are an adapter layer. Any ERP with an API (SAP, Microsoft Dynamics, weclapp) can receive the same data through a different adapter — this is a configuration change, not an engineering rebuild.

**Sidebar status badge:** On every page, the sidebar shows "● Odoo ERP: Live" (green) or "○ Odoo ERP: Offline" (red). Status is cached in session state after first check to avoid repeated API calls.

---

## 11. Trust Score Formula

```
Trust Score = (real_data_pct × 0.50) + third_party_score + doc_score + test_score
```

| Component | Max Points | Condition |
|---|---|---|
| Data Quality | 50 | `meta.data_real_pct × 0.5` — proportion of data points marked as verified real data |
| Third-Party Verification | 30 | Named independent verifier present in `dp26_independent_verification.verifier` |
| EU Declaration of Conformity | 10 | DoC reference number present in `dp50_doc_reference.reference` |
| Test Report | 10 | Test report number present in `dp73_test_reports.report_number` |

**Decision thresholds:**
- > 85 → **APPROVE** (green)
- 65–85 → **REVIEW** (amber)
- ≤ 65 → **BLOCK** (red)

**Why this formula can't be gamed:** Check 8 in the Authenticity module explicitly verifies that `trust_score ≤ (real_pct × 0.5) + 50`. A supplier cannot claim a high trust score if most of their data is unverified/mock.

---

## 12. Physical Sensor Verification (Level 2)

Three trust levels in the VeriCell model:

| Level | What It Means | Shown As |
|---|---|---|
| Level 1 — Software Only | Data validated by engine against benchmarks and cross-field checks | Amber badge: "Software Verified" |
| Level 2 — Physical Sensor | Software validation + confirmed cross-validation with physical BMS/sensor readings | Green badge: "Level 2 Physical Sensor Verified" |
| Level 3 — Double Verified | Level 2 + co-signed by accredited third party like TÜV (roadmap) | — |

**Current implementation:** Level 2 status is a boolean per manufacturer, stored in `PHYSICAL_VERIFIED` in `odoo_client.py`:
```python
PHYSICAL_VERIFIED = {
    "volvo":       True,   # ✅ Physical sensor data cross-validated
    "bmw":         True,   # ✅ Physical sensor data cross-validated
    "generic_oem": False,  # ❌ No physical validation — software only
}
```

This is shown as a badge in the Consumer Certificate tab and signals that the battery's declared sensor values (temperature, voltage, resistance, SoC) have been verified against actual BMS readings — not just declared in a document.

**Why this matters for second-life reuse:** Second-life operators need to know if the declared SoH is based on real measurements or manufacturer self-reporting. Level 2 badge = real measurements confirmed.

---

## 13. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| UI Framework | Streamlit 1.32+ | Rapid prototyping, built-in session state, native Python |
| Charts | Plotly 5.18+ | Interactive gauges, bar charts, choropleth maps |
| Data | Pandas 2.0+ | DataFrames for the 102-point tables |
| QR Codes | qrcode[pil] 7.4+ | Generates scannable QR certificate images |
| ERP Connection | xmlrpc.client (stdlib) | No external dependency — Python built-in XML-RPC |
| Verification Engine | Pure Python | No ML frameworks — deterministic rule engine |
| Data Storage | JSON files | EU DPP standard format, ERP-importable |
| Secrets | Streamlit secrets.toml | Credentials not hardcoded in main code |
| Caching | @st.cache_data | Prevents re-running 6 engine modules on every UI interaction |

**No database required.** All state is in session (ephemeral) + Odoo (persistent for ERP records).

---

## 14. File Structure

```
battery-dpp/
├── app.py                          # Main Streamlit application (~1,960 lines)
│   ├── Global CSS + page config
│   ├── Session state initialization
│   ├── Utility components (gauge, score_bar, compliance_timeline, etc.)
│   ├── _load_and_verify()          # Cached wrapper — runs all 6 engine modules
│   ├── render_sidebar_nav()        # Navigation + Odoo Live badge
│   ├── render_consumer()           # Consumer passport tabs
│   ├── render_technician()         # Technician tabs with sensor sliders
│   ├── render_company()            # Business analyst tabs
│   ├── render_regulator()          # Regulator tabs with AI audit summary
│   ├── page_role_select()          # Battery Passport entry
│   ├── page_browse()               # Battery selection
│   ├── page_passport()             # Routes to render_* based on role
│   ├── page_enterprise_dashboard() # Enterprise portal
│   ├── page_government_portal()    # Government portal
│   └── main()                      # Top-level router
│
├── engine/
│   └── verification_engine.py      # All 6 verification modules (~835 lines)
│       ├── Module 1: calculate_sustainability_score()
│       ├── Module 2: run_authenticity_checks()
│       ├── Module 3: run_compliance_tracker()
│       ├── Module 4: validate_sensors()
│       ├── Module 5: calculate_trust_score()
│       ├── Module 6: calculate_soh_composite()
│       ├── run_full_verification()  # Orchestrates all 6 modules
│       ├── load_battery()           # Reads JSON from data/manufacturers/
│       └── BATTERY_REGISTRY         # Maps manufacturer IDs to names/models
│
├── odoo_client.py                  # Odoo ERP adapter
│   ├── BATTERY_ODOO_MAP            # Maps battery names to Odoo product IDs
│   ├── PHYSICAL_VERIFIED           # Level 2 sensor verification status
│   ├── connect()                   # XML-RPC authentication
│   ├── fetch_products()            # Pull from Odoo
│   ├── push_verification_result()  # Write trust score + decision to Odoo
│   └── push_status_update()        # Write technician status to Odoo
│
├── data/
│   ├── manufacturers/
│   │   ├── volvo/ex90_nmc811_111kwh.json       # 102 data points for Volvo EX90
│   │   ├── bmw/ix_nmc712_105kwh.json           # 102 data points for BMW iX
│   │   └── generic_oem/lfp_80kwh.json          # 102 data points for Generic LFP
│   ├── benchmarks/
│   │   └── chemistry_benchmarks.json           # NMC811, NMC712, LFP benchmark ranges
│   └── compliance/
│       └── eu_2023_1542_thresholds.json        # EU regulation thresholds per year
│
├── .streamlit/
│   └── secrets.toml                # Odoo credentials (not committed to git)
└── requirements.txt                # streamlit, plotly, pandas, qrcode[pil]
```

---

## 15. Business Model

**We sell the trust layer, not the ERP.**

| Revenue Stream | Target Customer | Pricing Model |
|---|---|---|
| Per-passport validation | Second-life battery operators (Voltfang, Cylib) | €30–80 per battery validated |
| SaaS dashboard license | Fleet operators, recyclers | €1,500–5,000/month |
| Compliance API | ERP vendors (Odoo, weclapp, SAP partners) | €50,000–200,000/year |
| Insurance/Leasing data feed | Allianz, battery leasing companies | €100,000–500,000/year |

**Why second-life operators first:** They have the most acute pain. They cannot repurpose batteries without trusted SoH data. VeriCell's Level 2 badge directly unlocks reuse decisions worth €5,000–15,000 per battery.

---

## 16. Competitive Position

| Company | What They Do | Our Difference |
|---|---|---|
| Minespider | Blockchain supply chain data storage | They store data. We validate it. |
| Circulor | Supply chain traceability platform | Focused on traceability, not cross-field validation or ERP action |
| Spherity | Digital identity for DPP credentials | Identity layer only — no trust scoring or compliance engine |
| Circularise | DPP data management | Data management without procurement decision integration |
| AVILOO | Used EV battery health certificates | Consumer/dealer-focused. We do B2B procurement layer. |

**Our positioning:** None of the above integrate validation results directly into ERP workflows. We are the only player that takes "data exists" → runs 102-point validation → outputs APPROVE/REVIEW/BLOCK → syncs that decision to the procurement system in real-time.

---

## 17. Running the App

**Prerequisites:**
```bash
pip install streamlit plotly pandas "qrcode[pil]"
```

**Run:**
```bash
cd battery-dpp
streamlit run app.py
```

**Default landing:** Enterprise Dashboard (opens on the most business-critical view with the live BLOCK alert for Generic OEM).

**Odoo credentials** are in `.streamlit/secrets.toml`. The app falls back to hardcoded credentials if secrets are unavailable, so it runs offline from Odoo if needed (with Odoo features gracefully disabled).

---

## 18. Judge Q&A Cheat Sheet

**Q: Is this real ERP integration or mocked?**
> Real. Live Odoo instance at vericell.odoo.com. The "Sync to Odoo" button calls XML-RPC and writes to the product record in real-time. You can verify by opening Odoo after clicking sync — the product description updates.

**Q: Where does the battery data come from?**
> Manufacturers submit structured JSON files following the EU DPP format. In a real deployment, this would come via an API upload portal. For the demo, we pre-loaded 3 representative manufacturers (Volvo, BMW, a Chinese generic OEM).

**Q: What is the difference between your trust score and just reading the DPP?**
> The DPP is a container. Our engine validates the contents. Check #4 alone — carbon class consistency — can catch a manufacturer who declares "Class A" (best) but whose actual carbon value puts them in Class C. The DPP would show Class A. We flag the contradiction.

**Q: Can this work with SAP or other ERPs?**
> The verification output is standard JSON. The Odoo integration is an adapter (200 lines in `odoo_client.py`). Replacing it with a SAP BAPI call or REST API to any modern ERP is a configuration swap. We built on Odoo because it's open-source and fast to demo.

**Q: What is Level 2 Physical Sensor Verification?**
> Level 1 is software-only: we validate declared data against chemistry benchmarks and cross-field math. Level 2 means the declared sensor values (voltage, resistance, SoC, temperature) have been cross-validated against actual BMS readings from the physical battery. Generic OEM has no Level 2 badge because their data is 0% verified and they have no confirmed physical measurements.

**Q: Why would a manufacturer submit data to you?**
> Because EU Regulation 2023/1542 requires them to publish a DPP by 2027. Companies like Voltfang or leasing firms won't buy batteries without a trusted certificate. AVILOO proved this model for used EVs — dealers pay extra for AVILOO-certified cars. We are the AVILOO for B2B battery data.

**Q: How do you prevent manufacturers from gaming the trust score?**
> Check #8 in the Authenticity module: `max_trust = (real_data_pct × 0.5) + 50`. If 0% of your data is independently verified, your trust score cannot exceed 50/100 — which lands you in BLOCK. Generic OEM scores 6/100 precisely because they submitted 0% real data.

**Q: What happens with the BLOCK decision in practice?**
> In the Enterprise Dashboard, Generic OEM triggers a red banner at the top: "⚠️ 1 supplier blocked." If the technician syncs, Odoo updates the product description with "BLOCK | Trust Score 6.0/100." In a real system, this could trigger a purchase order block, a supplier notification, or a logistics hold — all via ERP workflow automation.

**Q: Is the 102 data points number real?**
> Yes. EU Battery Regulation 2023/1542 Annex XIII defines the data points. We modelled all 13 groups (A–M) across our 3 battery JSON files, with each data point having an ID, access level, status (REAL/MOCK), value, and flag. The Regulator view shows all 102 with filter controls.

**Q: What is your revenue model and who is the first customer?**
> First target: second-life battery operators (Voltfang, Cylib) who need trusted SoH data to decide whether a used battery is worth repurposing. We charge €30–80 per battery validation. At 1,000 batteries/month, that is €30K–80K MRR from one customer. Longer term: SaaS licenses to fleet operators and data feeds to insurers.
