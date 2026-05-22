# VeriCell — Technical Documentation

Full technical reference for the VeriCell verification engine, data model, and system architecture.

---

## Table of Contents

1. [Architecture & Data Flow](#1-architecture--data-flow)
2. [The Verification Engine — 6 Modules](#2-the-verification-engine--6-modules)
3. [The 102 Data Points — 13 Groups](#3-the-102-data-points--13-groups)
4. [EU Regulation Compliance Timeline](#4-eu-regulation-compliance-timeline)
5. [The 4 User Roles](#5-the-4-user-roles)
6. [The 3 Portal Views](#6-the-3-portal-views)
7. [Odoo ERP Integration](#7-odoo-erp-integration)
8. [Trust Score Formula](#8-trust-score-formula)
9. [Physical Sensor Verification](#9-physical-sensor-verification)
10. [File Structure](#10-file-structure)

---

## 1. Architecture & Data Flow

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
│  Module 4: Sensor Validator         (4 live sensor parameters)  │
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

**Key points:**
- Input is JSON — EU DPP standard format
- Output is ERP — decisions pushed to Odoo via XML-RPC (ERP-agnostic adapter)
- Engine is deterministic — same input always produces same output
- Caching — `@st.cache_data` prevents re-running 18 module executions per session

---

## 2. The Verification Engine — 6 Modules

All logic in `engine/verification_engine.py`.

### Module 1 — Sustainability Scorer

| Component | Weight | What It Checks |
|---|---|---|
| Carbon Footprint | 30% | Declared CO₂/kWh vs chemistry benchmark range |
| Recycled Content | 25% | Cobalt/Lithium/Nickel recycled % vs 2031 EU targets |
| Renewable Energy | 20% | % renewable in manufacturing (60% cell + 40% pack assembly) |
| Supply Chain Risk | 15% | Geopolitical + ESG risk scores per material origin country |
| Circularity | 10% | Recycling partners, EU take-back points, second-life eligibility |

### Module 2 — Authenticity Checker (8 Cross-Field Math Checks)

| # | Check | Formula |
|---|---|---|
| 1 | Energy Consistency | `V × Ah / 1000 = kWh` within 3% |
| 2 | Cell Count | `Modules × Cells per module = Total cells` exact |
| 3 | Carbon vs Benchmark | CO₂/kWh within chemistry range ± 15% |
| 4 | Carbon Class Match | Declared class matches calculated class from kg CO₂/kWh |
| 5 | Cobalt Weight | `mass × cathode_fraction × cobalt_pct` 50% tolerance |
| 6 | EU DoC Completeness | Reference number + notified body both present (Art. 18) |
| 7 | Supply Chain Traceability | OECD framework declared + independent verifier named |
| 8 | Trust Score Ceiling | `max_trust = (real_data_pct × 0.5) + 50` — ungameable |

### Module 3 — Compliance Tracker

| Year | Requirements |
|---|---|
| 2024 | EU DoC (Art. 18), CE marking (Art. 19), collection symbol (Art. 13) |
| 2027 | Carbon footprint (Art. 7), QR/DPP (Art. 13(6)), ISO battery ID |
| 2031 | Recycled Co ≥ 16%, Li ≥ 6%, Ni ≥ 6% (Art. 8) |
| 2036 | Co ≥ 26%, Li ≥ 12%, Ni ≥ 15% |

### Module 4 — Sensor Validator

| Sensor | Threshold | Effect |
|---|---|---|
| Temperature (°C) | Within chemistry operating range | CRITICAL if >10°C over max |
| Voltage (V) | Within ±10% of nominal | CRITICAL if >10% deviation |
| Internal Resistance (mΩ) | % increase from baseline | CRITICAL if >50% increase |
| State of Charge (%) | 10–90% | WARNING if <10% |

SoH estimation: every 20% resistance increase ≈ 5% SoH loss (NMC aging curve).

### Module 5 — Trust Score Calculator

See [Section 8](#8-trust-score-formula).

### Module 6 — SoH Composite

| Parameter | Weight |
|---|---|
| Remaining Capacity | 35% |
| Remaining Power | 25% |
| Round-Trip Efficiency | 20% |
| Self-Discharge Rate | 10% |
| Resistance Health | 10% |

Output: composite score + label (EXCELLENT / GOOD / MODERATE / POOR / CRITICAL)

---

## 3. The 102 Data Points — 13 Groups

| Group | Label | Key Data Points |
|---|---|---|
| A | General Info | Manufacturer, model, chemistry, capacity |
| B | Carbon Footprint | kg CO₂e/kWh, carbon class (A/B/C/D), lifecycle phases |
| C | Recycled Content | % cobalt, lithium, nickel recycled; renewable energy in manufacturing |
| D | Responsible Sourcing | Country of origin per material, OECD due diligence |
| E | Electrical Characteristics | Nominal voltage, capacity (Ah), C-rate, temperature range |
| F | Conformity & Labelling | EU DoC, CE marking, QR code, waste symbol |
| G | Composition & Disassembly | Cell count, module structure, material mass breakdown |
| H | Authority Information | Notified body, test reports, market surveillance contacts |
| I | Individual Performance | Charge/discharge cycles, efficiency curves |
| J | State of Health | Remaining capacity %, power %, efficiency, self-discharge, resistance |
| K | Expected Lifetime | Rated cycle life, calendar life, warranty terms |
| L | Operational Data | Temperature log, SoC at delivery, negative events |
| M | Identification & Metadata | ISO/IEC 15459-1 battery ID, QR code, DPP URL |

**Access levels:** L1 Consumer · L2 Technician · L3 Business · L4 Regulator only

---

## 4. EU Regulation Compliance Timeline

**Regulation:** EU 2023/1542 — entered into force 17 August 2023.

| Year | Mandatory |
|---|---|
| 2024 | EU DoC, CE marking, separate collection symbol, manufacturer ID |
| 2027 | QR code linking to DPP, carbon footprint declaration, performance class |
| 2031 | Recycled Co ≥ 16%, Li ≥ 6%, Ni ≥ 6% |
| 2036 | Co ≥ 26%, Li ≥ 12%, Ni ≥ 15% |

---

## 5. The 4 User Roles

**Consumer (L1)** — Trust certificate + QR code + health gauge + plain-language summary + recycling info

**Technician (L2)** — Full SoH breakdown + live sensor sliders + real-time anomaly detection + disassembly info + Odoo sync

**Business Analyst (L3)** — Sustainability score (5 components) + carbon lifecycle chart + supply chain risk + compliance timeline + all 102 data points filterable

**Regulator (L4)** — AI Audit Summary + full 8-check authenticity audit + complete trust score breakdown + unredacted 102 points + downloadable HTML audit report

---

## 6. The 3 Portal Views

**Enterprise Dashboard** — Default landing. BLOCK alert banner + supplier risk matrix + KPI strip + drill-down per battery + Odoo sync button

**Government Portal** — EU compliance choropleth map + violation analysis bar chart + per-battery audit reports with download

**Battery Passport** — Role-select → battery browse → role-appropriate passport view. Consumer gets QR certificate as first tab.

---

## 7. Odoo ERP Integration

```python
# Connection: Python stdlib only — no external library
import xmlrpc.client

# Live instance: https://vericell.odoo.com

# Three operations:
fetch_products()           # ERP → App: pulls product list
push_verification_result() # App → ERP: writes Trust Score + decision
push_status_update()       # App → ERP: writes technician status
```

Adapter pattern: verification output is standard JSON. Replacing Odoo with SAP BAPI or any REST ERP = configuration change only.

---

## 8. Trust Score Formula

```
Trust Score = (real_data_pct × 0.50) + third_party_score + doc_score + test_score
```

| Component | Max | Condition |
|---|---|---|
| Data Quality | 50 | `real_data_pct × 0.5` |
| Third-Party Verification | 30 | Named independent verifier present |
| EU Declaration of Conformity | 10 | DoC reference number present |
| Test Report | 10 | Test report number present |

Thresholds: > 85 → APPROVE · 65–85 → REVIEW · ≤ 65 → BLOCK

Anti-gaming: `trust_score ≤ (real_pct × 0.5) + 50` enforced by Check #8.

---

## 9. Physical Sensor Verification

| Level | Meaning | Badge |
|---|---|---|
| Level 1 | Software-only validation against benchmarks | Amber: "Software Verified" |
| Level 2 | Software + cross-validation with physical BMS readings | Green: "Level 2 Physical Sensor Verified" |
| Level 3 | Level 2 + TÜV co-signed (roadmap) | — |

```python
PHYSICAL_VERIFIED = {
    "volvo":       True,   # ✅ Physical sensor data cross-validated
    "bmw":         True,   # ✅ Physical sensor data cross-validated
    "generic_oem": False,  # ❌ No physical validation — software only
}
```

---

## 10. File Structure

```
battery-dpp/
├── app.py                          # Main Streamlit app (~1,960 lines)
├── engine/
│   └── verification_engine.py      # All 6 modules (~835 lines)
├── odoo_client.py                  # Odoo ERP adapter
├── data/
│   ├── manufacturers/
│   │   ├── volvo/ex90_nmc811_111kwh.json
│   │   ├── bmw/ix_nmc712_105kwh.json
│   │   └── generic_oem/lfp_80kwh.json
│   ├── benchmarks/
│   │   └── chemistry_benchmarks.json
│   └── compliance/
│       └── eu_2023_1542_thresholds.json
├── .streamlit/
│   └── secrets.toml
└── requirements.txt
```
