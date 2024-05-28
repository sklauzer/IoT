import pandas as pd
import os
from typing import List, Dict, Tuple
import dirs
import tqdm
from colorama import Fore, Style

def load_data(data_dir:str) -> pd.DataFrame:
    """
    Load data from files in the specified directory with the given file extension.

    Parameters:
    - data_dir (str): The directory path where the data files are located.
    """
    
    print(Style.BRIGHT + Fore.LIGHTMAGENTA_EX + "Loading Data")
    print(Style.RESET_ALL)
    
    df_list = []
    errors = []
    for file_name in tqdm.tqdm(os.listdir(data_dir)):
        if file_name.endswith(".dat"):
            fpath = os.path.join(data_dir, file_name)
            try:
                df = pd.read_csv(fpath, sep=";", skiprows=1)
                df_list.append(df)
            except Exception as e:
                errors.append(f"Error loading file {file_name}: {e}")
    
    for e in errors:
        print('\n')
        print(Fore.RED + e)
        print(Style.RESET_ALL)

    print("✓ Done")
    print("\n")

    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
    

def preprocess_data(df:pd.DataFrame) -> pd.DataFrame:
    """
    Preprocesses a pandas DataFrame.
    
    Args:
        df pd.DataFrame: A pandas DataFrame to be preprocessed.
    """
    print(Style.BRIGHT +  Fore.LIGHTMAGENTA_EX + "Preprocessing Data")
    print(Style.RESET_ALL)

    # ----- Convert to time format ------------------
    df["date_time"] = pd.to_datetime(df["date_time"])

    # ----- Strip the whitespace --------------------
    df["device_id"] = df["device_id"].str.strip()

    df['snr'] = df['snr'].str.strip().astype(float)

    # ------------------------------------------------
    # Add additional preprocessing steps here
    # ...
    # ------------------------------------------------

    print("✓ Done")
    print("\n")

    return df

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds additional features to the given DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to which the features will be added.
    """
    
    print(Style.BRIGHT + Fore.LIGHTMAGENTA_EX + "Adding Features")
    print(Style.RESET_ALL)

    # ----- Room -------------------------------------
    def extract_room(device_id):
        room = device_id.replace("hka-aqm-n", "")
        return room
    
    df['room'] = df['device_id'].apply(extract_room)

    # ----- Floor -------------------------------------
    def extract_floor(device_id):
        floor = int(device_id.replace("hka-aqm-n", "")[0])
        return floor

    df['floor'] = df['device_id'].apply(extract_floor)

    print("✓ Done")
    print("\n")
    
    return df

def save_data(df:pd.DataFrame, output_fpath:str) -> None:
    print(Style.BRIGHT + Fore.LIGHTMAGENTA_EX + "Saving Data")
    print(Style.RESET_ALL)

    """
    Save the given DataFrame to a Parquet file.

    Args:
        df (pandas.DataFrame): The DataFrame to be saved.
        output_path (str): The path to save the Parquet file.
    """

    df.to_parquet(output_fpath, index=False)

    print("✓ Done")
    print("\n")

def pipeline(data_dir:str=None, output_fpath:str=None) -> bool:
    """
    A function that performs a data pipeline process.

    Args:
        data_dir (str): The directory path where the data (all .dat files) is located.
        output_fpath (str): The file path to save the processed data.

    Returns:
        bool: True if the pipeline process is successful, False otherwise.
    """

    working_dir = dirs.set_working_dir()
    if data_dir is None:
        data_dir = os.path.join(working_dir, "data")
    if output_fpath is None:
        output_fpath = os.path.join(working_dir, "data/output.parquet")

    df = load_data(f"{data_dir}/hka-aqm-n")
    df_preprocessed = preprocess_data(df)
    df_features = add_features(df_preprocessed)
    save_data(df_features, output_fpath)
    return True

# Hauptausführung
if __name__ == "__main__":
    print(pipeline())

    
