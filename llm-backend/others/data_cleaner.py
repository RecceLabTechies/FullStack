import pandas as pd
import json


def identify_file_type(data):
    """Identify the type of data file based on its structure"""
    # Check first record's keys
    first_record = data[0]

    # If these keys exist, it's an ad campaign file
    if all(key in first_record for key in ["Campaign_ID", "Channel_Name", "Spending"]):
        return "ad_campaign"
    # If these keys exist, it's a banking KPI file
    elif all(
        key in first_record for key in ["Number_of_New_Accounts", "Total_Base_Mn"]
    ):
        return "banking_kpi"
    else:
        raise ValueError("Unknown file type")


def clean_ad_campaign_data(df):
    """Clean advertisement campaign performance data"""
    # Convert numeric columns to appropriate types
    numeric_columns = ["Spending", "Number_of_Views", "Number_of_Leads"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert Time to datetime
    df["Time"] = pd.to_datetime(df["Time"], format="%b-%y")

    # Clean up categorical columns
    df["Channel_Name"] = df["Channel_Name"].str.strip()
    df["Age_group"] = df["Age_group"].str.strip()
    df["Campaign_ID"] = df["Campaign_ID"].str.strip()

    return df


def clean_banking_kpi_data(df):
    """Clean banking KPI data"""
    # Convert numeric columns to appropriate types
    numeric_columns = ["Number_of_New_Accounts", "Total_Base_Mn"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert Time to datetime
    df["Time"] = pd.to_datetime(df["Time"], format="%b-%y")

    return df


def clean_data(file_path):
    """Main function to clean data files"""
    try:
        # Read JSON file
        with open(file_path, "r") as file:
            data = json.load(file)

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Identify file type
        file_type = identify_file_type(data)

        # Clean based on file type
        if file_type == "ad_campaign":
            return clean_ad_campaign_data(df)
        else:  # banking_kpi
            return clean_banking_kpi_data(df)

    except Exception as e:
        raise Exception(f"Error processing file {file_path}: {str(e)}")


def process_directory(input_dir, output_dir):
    """Process all JSON files in a directory and save cleaned data

    Args:
        input_dir (str): Path to directory containing input JSON files
        output_dir (str): Path to directory where cleaned JSON files will be saved
    """
    import os

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Process each JSON file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"cleaned_{filename}")

            try:
                # Clean the data
                cleaned_df = clean_data(input_path)

                # Convert DataFrame to JSON and save
                cleaned_data = cleaned_df.to_dict("records")
                with open(output_path, "w") as f:
                    json.dump(cleaned_data, f, indent=2, default=str)

                print(f"Successfully processed {filename}")

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python data_cleaner.py input_directory output_directory")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    process_directory(input_dir, output_dir)
