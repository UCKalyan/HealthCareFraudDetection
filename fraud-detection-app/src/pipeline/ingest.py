import os
import shutil
import datetime
import yaml
import pandas as pd
import logging
import subprocess
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataIngestion")

class DataIngestionPipeline:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir / "data/input_files"
        self.output_dir = self.base_dir / "data/output_files"
        self.processed_dir = self.base_dir / "data/processed_data"
        self.config_path = self.base_dir / "src/pipeline/pipeline_config.yaml"
        
        self.config = self._load_config()
        self._ensure_directories()

    def _load_config(self):
        if not self.config_path.exists():
            logger.error(f"Config file not found at {self.config_path}")
            raise FileNotFoundError("Pipeline config missing")
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _ensure_directories(self):
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def detect_file_type(self, filename: str) -> str:
        """Identify file type based on naming conventions."""
        filename = filename.lower()
        if "mup_phy" in filename or "physician" in filename:
            return "part_b"
        elif "mup_dpr" in filename or "prescriber" in filename:
            return "part_d"
        elif "dme" in filename:
            return "dme"
        elif "leie" in filename or "exclude" in filename:
            return "leie"
        return "unknown"

    def standardize_columns(self, df: pd.DataFrame, file_type: str, year: str = "default") -> pd.DataFrame:
        """Rename columns to internal standard based on config."""
        mappings = self.config['mappings'].get(file_type, {})
        
        # Try specific year, fallback to default
        year_map = mappings.get(year, mappings.get('default', {}))
        
        # Invert map for renaming: {ExternalName: InternalName}
        rename_map = {v: k for k, v in year_map.items()}
        
        # Only rename columns that exist
        actual_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        
        if actual_rename:
            logger.info(f"Renaming {len(actual_rename)} columns for {file_type}")
            df = df.rename(columns=actual_rename)
        
        return df

    def process_files(self):
        """Main execution method to process all files in input directory."""
        files = list(self.input_dir.glob("*.csv"))
        if not files:
            logger.info("No CSV files found in input directory.")
            return

        logger.info(f"Found {len(files)} files to process.")
        
        # Create batch archive folder
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.output_dir / f"batch_{timestamp}"
        batch_dir.mkdir()

        processed_count = 0

        for file_path in files:
            try:
                logger.info(f"Processing {file_path.name}...")
                
                file_type = self.detect_file_type(file_path.name)
                if file_type == "unknown":
                    logger.warning(f"Skipping unknown file type: {file_path.name}")
                    continue

                # Load Data
                # Using low_memory=False for large CMS files, or specify dtypes in production
                df = pd.read_csv(file_path, low_memory=False)
                
                # Standardize
                # TODO: Extract year from filename if possible, currently using default
                df = self.standardize_columns(df, file_type)

                # Save Standardized Version
                output_name = f"{file_type}_{timestamp}.parquet"
                df.to_parquet(self.processed_dir / output_name)
                logger.info(f"Saved processed data to {output_name}")

                # Archive Original
                if self.config['settings']['archive_processed_files']:
                    shutil.move(str(file_path), str(batch_dir / file_path.name))
                    logger.info(f"Archived {file_path.name}")
                
                processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {str(e)}")

        if processed_count > 0:
            logger.info(f"Successfully processed {processed_count} files.")
            # Here we would trigger the training pipeline
            self.trigger_training()
        else:
            logger.info("No files were successfully processed.")

    def trigger_training(self):
        """Triggers the full model training pipeline."""
        logger.info("Triggering model retraining (main.py)...")
        try:
            # Run main.py from the project root
            subprocess.run(["python", "main.py"], cwd=self.base_dir, check=True)
            logger.info("Model retraining completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Model retraining failed: {e}")

if __name__ == "__main__":
    # Run pipeline assuming script is run from project root
    pipeline = DataIngestionPipeline(os.getcwd())
    pipeline.process_files()
