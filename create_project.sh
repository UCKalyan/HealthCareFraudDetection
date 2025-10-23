#!/bin/bash

# This script sets up the directory structure for the Healthcare Fraud Detection project.

echo "Creating project directories..."

# Create root directories
mkdir -p data/raw_data
mkdir -p data/processed_data
mkdir -p notebooks
mkdir -p src/data_processing
mkdir -p src/models
mkdir -p src/training
mkdir -p src/utils
mkdir -p saved_models
mkdir -p reports

echo "Creating initial Python script files..."

# Create Python files with placeholders
touch src/__init__.py
touch src/data_processing/__init__.py
touch src/data_processing/loader.py
touch src/data_processing/preprocessor.py
touch src/models/__init__.py
touch src/models/adaptive_deep_model.py
touch src/training/__init__.py
touch src/training/train.py
touch src/utils/__init__.py
touch src/utils/evaluation.py
touch main.py
touch requirements.txt

# Create a placeholder notebook
touch notebooks/01_EDA.ipynb

echo "Creating README.md..."

# Create README.md file
cat <<'EOF' > README.md
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
EOF

echo "Project structure created successfully."
echo "Next steps:"
echo "1. Place downloaded datasets in data/raw_data/"
echo "2. Create a Python virtual environment and install dependencies from requirements.txt"
echo "3. Start developing the code in the 'src' directory."
