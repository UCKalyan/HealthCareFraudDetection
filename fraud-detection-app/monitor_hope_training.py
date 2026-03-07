import time
import os
import sys

def monitor_log(log_file):
    print(f"--- 📡 Monitoring HOPE Training Logs ({log_file}) ---")
    print(f"{'Step':<10} | {'Avg Divergence':<20} | {'Max Divergence':<20}")
    print("-" * 60)
    
    # Wait for file creation if it doesn't exist
    if not os.path.exists(log_file):
        print("Waiting for log file to be created...", end='\r')
        
    try:
        # Keep trying to open the file until it exists
        while not os.path.exists(log_file):
            time.sleep(1)
            
        with open(log_file, 'r') as f:
            # Go to the end of the file initially if you only want new updates
            # f.seek(0, os.SEEK_END)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                    
                if "Step" in line and "Divergence" in line:
                    try:
                        # Parse line: [Timestamp] Step 50 | Avg Divergence: 0.123 | Max Divergence: 0.456
                        if "Step" in line:
                            parts = line.split('|')
                            step_part = [p for p in parts if "Step" in p][0]
                            avg_part = [p for p in parts if "Avg Divergence" in p][0]
                            max_part = [p for p in parts if "Max Divergence" in p][0]
                            
                            step = step_part.split('Step')[1].strip()
                            avg_div = avg_part.split(':')[1].strip()
                            max_div = max_part.split(':')[1].strip()
                            
                            print(f"{step:<10} | {avg_div:<20} | {max_div:<20}")
                    except (IndexError, ValueError) as e:
                        # Pass on malformed lines
                        pass
                        
    except KeyboardInterrupt:
        print("\n--- Monitoring Stopped ---")

if __name__ == "__main__":
    # Default path assuming script is in fraud-detection-app/
    LOG_FILE = "logs/hope_updates.log"
        
    monitor_log(LOG_FILE)
