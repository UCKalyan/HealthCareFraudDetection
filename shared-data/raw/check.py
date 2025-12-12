import pandas as pd

def show_csv_columns(file_path):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Display column names
    print("Columns in the CSV:")
    for col in df.columns:
        print(col)

# Example usage
if __name__ == "__main__":
    file_path = "MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv"
    show_csv_columns(file_path)

