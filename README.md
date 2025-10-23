# Adaptive and Explainable AI for Healthcare Fraud Detection

This repository contains the code and resources for the M.Tech project on detecting healthcare fraud using adaptive deep learning and explainable AI.

## Project Structure

- `data/`: Contains raw and processed datasets.
  - `raw_data/`: Place the initial downloaded CMS datasets here.
  - `processed_data/`: Stores cleaned and preprocessed data ready for model training.
- `notebooks/`: Jupyter notebooks for exploratory data analysis (EDA) and experimentation.
- `src/`: Source code for the project.
  - `data_processing/`: Scripts for loading and preprocessing data.
  - `models/`: Contains the definition of the deep learning model.
  - `training/`: Scripts for training the model.
  - `utils/`: Utility functions for evaluation, logging, etc.
- `saved_models/`: Directory to save trained model weights.
- `reports/`: Project reports and generated figures.
- `main.py`: Main script to run the entire pipeline (data processing, training, evaluation).
- `requirements.txt`: Python dependencies for the project.

## Datasets

The project uses public datasets from the Centers for Medicare & Medicaid Services (CMS).

1.  **Medicare Part D Prescriber Data:** [Download Link](https://www.cms.gov/Research-Statistics-Data-and-Systems/Statistics-Trends-and-Reports/Medicare-Provider-Charge-Data/Part-D-Prescriber)
2.  **Medicare Physician & Other Supplier Data:** [Download Link](https://www.cms.gov/Research-Statistics-Data-and-Systems/Statistics-Trends-and-Reports/Medicare-Provider-Charge-Data/Physician-and-Other-Supplier)

Please download the relevant files and place them in the `data/raw_data/` directory.

## Setup and Installation

1.  Clone the repository:
    ```bash
    git clone <your-repo-link>
    cd <your-repo-name>
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  **Preprocess the data:** Update the data loading paths in `src/data_processing/loader.py` and run the preprocessing script.
2.  **Train the model:** Execute the main training script.
    ```bash
    python main.py
    ```

## Base Paper

This project is based on the concepts from:
J, P., A, S., G, S., & P, M. (2024). "Healthcare fraud detection using adaptive learning and deep learning techniques." *Evolving Systems*.
DOI: `10.1007/s12530-023-09514-6`


## How to Test Your Final Application
Build Artifacts (Run Once): python build_artifacts.py

Start Backend: uvicorn api_server:app --reload

Open Frontend: Open fraud_workbench_ui.html in your browser.

Test Both Workflows:

Existing Provider: Use the "NPI Lookup" for a provider like 1003000126.

New Provider: Click "Manual Analysis," fill out the form, and click "Analyze New Provider."


## As an expert data analyst and information architect, let's break this down in detail.

Part 1: Decoding Your Provider's Feature Profile
The values you provided represent a single provider's "digital fingerprint" as seen by our model. Let's interpret each one to build a complete picture.

Provider's Fingerprint:

cost_per_service: 117.13

services_per_bene: 2.21

pagerank_centrality: 0.00

provider_archetype_0: 1.00 (and 0 for all others)

1. cost_per_service: 117.13
What It Is: This is the provider's average charge for every single service they perform or prescription they write. It's calculated as Total Claim Cost / Total Services.

What This Value Means: For this provider, each action they take (a procedure, a consultation, a prescription) generates an average of $117.13 in claims. The model doesn't see this number in isolation; it sees how this number compares to thousands of other providers.

How It Relates to Fraud: This is a primary indicator for upcoding or billing for unnecessarily expensive services. A fraudulent provider might bill for a complex, 45-minute consultation when they only performed a simple 10-minute check-up. This would dramatically inflate their cost_per_service compared to their honest peers.

2. services_per_bene: 2.21
What It Is: This is the average number of services or prescriptions this provider gives to each unique patient (beneficiary) they see. It's calculated as Total Services / Total Beneficiaries.

What This Value Means: This provider performs, on average, 2.21 distinct services for each patient in their care over the year. This could be one initial visit and one follow-up, for example.

How It Relates to Fraud: This is a primary indicator for overutilization or "ping-ponging." A fraudulent provider might require patients to come back for numerous unnecessary follow-up visits, each one generating a new bill. This would drive their services_per_bene value much higher than that of an ethical provider in the same specialty.

3. pagerank_centrality: 0.00
What It Is: This is a measure of the provider's "influence" or "centrality" within the healthcare network we built. We created a graph where providers are linked to the medical specialties they practice.

What This Value Means: A score of 0.00 is very low. It means this provider is on the periphery of the network. They might be in a common specialty with many other providers, or in a specialty that is not highly connected to others.

How It Relates to Fraud: A very high PageRank score can sometimes be suspicious, as it might indicate a "hub" provider who is a key player in a large, potentially collusive network. A low score, like this one, is generally a sign of normal, non-central activity and is less suspicious to the model.

4. provider_archetype_0: 1.00
What It Is: Our K-Means clustering algorithm analyzed all providers based on their cost_per_service and services_per_bene. It then grouped them into 5 distinct "behavioral archetypes." This provider's behavior was most similar to the providers in "Cluster 0."

What This Value Means: This provider belongs to Archetype 0. The model doesn't just see this provider's individual stats; it sees them as a member of a group.

How It Relates to Fraud: This is one of the most powerful features. The model learns the collective risk of the entire group. For instance, Archetype 0 might be the "Low-Cost, Low-Volume General Practitioners," which the model will learn is a very low-risk group. Conversely, another archetype, say "Archetype 3," might be the "High-Cost, High-Service Pain Management Specialists," which the model will learn is an inherently high-risk group. This feature allows the model to capture the risk profile of a provider's entire business model, not just their raw numbers.

Part 2: Fraud Scenarios Our Current Model is Designed to Detect
Your current system is primarily an anomaly detection engine. It is built on the fundamental assumption that fraudulent behavior, while diverse, results in a provider becoming a statistical outlier compared to their direct peers.

The primary mechanism for this is the Z-Score, which we use to create the training labels.

We define a provider as "suspicious" if their billing behavior is significantly different from the average behavior of other providers in their same medical specialty.

Therefore, our model is explicitly designed to detect the following scenarios:

Upcoding and Overbilling: A cardiologist who consistently bills for procedures that are far more expensive than the average cardiologist. This would result in a very high Cost Z-Score, the primary flag our model learns from.

Service Overutilization: A dermatologist who requires patients to have far more follow-up visits than the average dermatologist for the same condition. This increases their services_per_bene and total cost, which the model will identify as anomalous.

Outlier Prescribing Patterns: A general practitioner who prescribes an unusually high volume of expensive, brand-name drugs compared to their peers who prescribe cheaper generics. This would also lead to a high Cost Z-Score.

Part 3: Other Fraud Scenarios to Consider (Future Work)
Your current model is powerful, but the world of fraud is vast. For your M.Tech report's "Future Work" section, you can propose expanding the system to detect these more sophisticated schemes:

Collusive Networks & Kickbacks:

Scenario: A doctor consistently refers all their patients to a single diagnostic lab or pharmacy, who in turn gives the doctor a "kickback" (a secret payment).

How to Detect: This requires building a heterogeneous graph with different node types (Providers, Patients, Pharmacies, Labs). By analyzing the flow of patients, you can identify unusually strong and exclusive relationships. A provider-pharmacy pair that shares 95% of their patients is highly suspicious.

Identity Theft & Phantom Billing:

Scenario: A criminal uses a stolen provider NPI and a list of stolen patient IDs to bill for services that never occurred.

How to Detect: This requires looking for impossible scenarios in more granular, event-level data (not just annual summaries). For example:

A provider billing for 30 hours of services in a 24-hour day.

A patient receiving services in New York and California on the same day.

Unbundling of Services:

Scenario: A surgeon performs a knee replacement. Instead of billing with one comprehensive code for the surgery, they bill separately for the incision, the implant, the sutures, and the post-op check. The sum of the parts is greater than the whole.

How to Detect: This requires a deep analysis of the procedure codes (HCPCS and DRG codes) themselves. The model would need to learn which combinations of codes are medically nonsensical or violate billing rules. This often involves Natural Language Processing (NLP) on the code descriptions.

Temporal Anomalies (Sudden Changes in Behavior):

Scenario: A provider has a stable, low-risk billing pattern for five years and then, in a single year, their billing volume and costs triple without any change in their specialty or location. This could indicate that their practice has been taken over for fraudulent purposes.

How to Detect: This requires time-series analysis. You would need to process the CMS data year-over-year and engineer features that measure the rate of change in a provider's behavior. A high rate of change is a significant red flag.