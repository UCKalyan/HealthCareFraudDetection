# Shared Data Directory

Common data storage for both Fraud Detection and Finance applications.

## Structure

```
shared-data/
├── raw/            # Raw Medicare CMS datasets
├── processed/      # Processed features and profiles
└── databases/      # SQLite databases
```

## Usage

Both applications access this data via symlinks:
- `fraud-detection-app/data` → `../shared-data`
- `finance-app/data` → `../shared-data`

## Data Files

- **Raw Data:** Medicare Part B, Part D, NPPES, LEIE
- **Processed:** Feature stores, financial profiles
- **Databases:** providers.db, finance.db, feedback.db
