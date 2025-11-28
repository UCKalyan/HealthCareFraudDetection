# Data Quality and Distribution Report

## 1. Dataset Overview
- **Total Records:** 1767599
- **Total Features:** 21

## 2. Dataset Definitions & Statistics
**Data Year:** 2023

### Medicare Part B (Physician & Other Practitioners)
- **File Name:** `MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv`
- **Total Records:** 9,660,648
- **Structure:** **Procedure-Level** (Aggregated by NPI, HCPCS Code, and Place of Service).
- **Definition:** This dataset provides detailed claims information for each procedure performed by a physician. As noted in research (e.g., Herland et al., 2018), each row represents a unique combination of:
    1.  **NPI** (Performing Provider)
    2.  **HCPCS Code** (Procedure/Service)
    3.  **Place of Service** (Facility vs. Non-Facility)
- **Usage:** Allows for granular analysis of specific procedures (e.g., detecting if a provider is billing for an impossible number of complex surgeries).

### Medicare Part D (Prescriber)
- **File Name:** `MUP_DPR_RY25_P04_V10_DY23_NPI.csv`
- **Total Records:** 1,380,666
- **Structure:** **Provider-Level** (Aggregated by NPI).
- **Definition:** This dataset aggregates prescription data for each provider. Each row represents a single provider and summarizes their total prescribing activity (total claims, total drug cost, opioid claims, etc.) for the year.
- **Usage:** Used to identify high-level prescribing anomalies (e.g., high opioid rates, high average drug costs).

### LEIE (List of Excluded Individuals/Entities)
- **Definition:** A database maintained by the OIG listing individuals excluded from federally funded healthcare programs.
- **Usage:** Serves as the **Ground Truth** (Labels). Providers in this list are labeled as "Fraud" (1).

### Data Combination & Overlap Analysis
The **Part B** and **Part D** datasets are merged using an **Outer Join** on the unique **National Provider Identifier (NPI)** to preserve all provider data.

**Overlap Statistics:**
- **Total Unique Providers (Union):** 1,767,599
- **Providers in BOTH Part B and Part D:** 788,347 (44.6%)
- **Providers in Part B ONLY:** 386,934 (21.9%)
- **Providers in Part D ONLY:** 592,318 (33.5%)

**Missing Data Implication:**
- Providers present in only one dataset will have `0` values for features from the missing dataset. For example, a provider in "Part B Only" will have `total_drug_cost = 0`.
- This is handled by the model, which learns patterns for "Procedure-Only" vs "Prescription-Only" providers.

### LEIE (List of Excluded Individuals/Entities)
- **Total Records:** 82,290
- **Unique NPIs:** 8,172
- **Matches in Our Dataset:** 361
- **Current Usage:** **UNUSED**.
    - **Important Note:** The current pipeline generates **synthetic labels** based on statistical anomalies (Z-score > 3.0 on Claim Cost). It does **not** currently use the LEIE list to label fraud.
    - **Recommendation:** Future iterations should integrate LEIE to validate the synthetic labels or switch to supervised learning using these 361 confirmed fraud cases.

## 3. Provider Specialties
- **Total Unique Specialties:** 105
### Top 20 Specialties
| Specialty | Count | Percentage |
|---|---|---|
| 0 | 592318 | 33.51% |
| Nurse Practitioner | 174681 | 9.88% |
| Physician Assistant | 94996 | 5.37% |
| Internal Medicine | 88703 | 5.02% |
| Family Practice | 78514 | 4.44% |
| Physical Therapist in Private Practice | 73457 | 4.16% |
| Emergency Medicine | 47236 | 2.67% |
| Certified Registered Nurse Anesthetist (CRNA) | 38387 | 2.17% |
| Anesthesiology | 34189 | 1.93% |
| Chiropractic | 32225 | 1.82% |
| Diagnostic Radiology | 31554 | 1.79% |
| Optometry | 29720 | 1.68% |
| Mass Immunizer Roster Biller | 28317 | 1.60% |
| Orthopedic Surgery | 20699 | 1.17% |
| Cardiology | 19399 | 1.10% |
| Hospitalist | 19105 | 1.08% |
| General Surgery | 19058 | 1.08% |
| Psychiatry | 18253 | 1.03% |
| Obstetrics & Gynecology | 17962 | 1.02% |
| Ophthalmology | 17001 | 0.96% |

![Top Specialties](figures/top_specialties.png)

## 4. Numerical Feature Statistics
|                    |       Mean |     Median |    Std Dev |   Min |              Max |
|:-------------------|-----------:|-----------:|-----------:|------:|-----------------:|
| total_service_cost |   2278.14  |  512.12    |   8897.43  |     0 | 975616           |
| total_services     |   1496.71  |  136       |  30837.6   |     0 |      1.60197e+07 |
| total_benes_phys   |    466.588 |   77       |  15514.6   |     0 |      1.04037e+07 |
| total_drug_cost    | 155945     | 4505.03    | 575518     |     0 |      1.60292e+08 |
| total_scripts      |    914.057 |  104       |   2715.61  |     0 | 666251           |
| total_benes_presc  |    124.774 |   42       |    791.902 |     0 | 492011           |
| cost_per_service   |    103.317 |   31.2081  |    601.535 |     0 | 355925           |
| services_per_bene  |      4.335 |    2.02404 |    167.652 |     0 | 137140           |

### Feature Distributions (Log Scale for Skewed Data)
#### total_service_cost
![Distribution of total_service_cost](figures/dist_total_service_cost.png)

#### total_services
![Distribution of total_services](figures/dist_total_services.png)

#### total_benes_phys
![Distribution of total_benes_phys](figures/dist_total_benes_phys.png)

#### total_drug_cost
![Distribution of total_drug_cost](figures/dist_total_drug_cost.png)

#### total_scripts
![Distribution of total_scripts](figures/dist_total_scripts.png)

#### total_benes_presc
![Distribution of total_benes_presc](figures/dist_total_benes_presc.png)

#### cost_per_service
![Distribution of cost_per_service](figures/dist_cost_per_service.png)

#### services_per_bene
![Distribution of services_per_bene](figures/dist_services_per_bene.png)

