import os
import subprocess
import sys

current_dir = os.getcwd()
git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=current_dir)
git_root = git_root.decode("utf-8").strip()
os.chdir(git_root)
new_dir = os.getcwd()
sys.path.append(git_root)

import pandas as pd
from typing import List, Dict, Tuple
import utils.dirs
import tqdm
from colorama import Fore, Style
import utils.weather

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

    if "snr" in df.columns and df["snr"].dtype == "object":
        df['snr'] = df['snr'].str.strip().astype(float)

    #----- Data Cleaning ----------------------------
    # Temperature
    df = df[(df["tmp"] > -20) & (df["tmp"] < 50)]

    # Humidity
    df = df[(df["hum"] > 0) & (df["hum"] < 100)]

    # CO2
    df = df[(df["CO2"] > 0) & (df["CO2"] < 10000)]

    # VOC
    df = df[(df["VOC"] > 0) & (df["VOC"] < 10000)]

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove rows with NaN values in the used columns
    df = df.dropna(subset=['tmp', 'hum', 'CO2', 'VOC'])

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

    #----- Add date -----------------------------------
    df["date"] = df["date_time"].dt.date

    #----- Add the month ------------------------------
    df["month"] = df["date_time"].dt.month

    #----- Add the time of day ------------------------
    df["hour"] = df["date_time"].dt.hour

    #----- Add the day of the week --------------------
    df["day_of_week"] = df["date_time"].dt.dayofweek

    #----- Add weekend or not -------------------------
    df['is_weekend'] = df['day_of_week'] >= 5

    #----- Add the season based on the month (Germany) -
    df["season"] = df["month"].map({
        1: "winter",
        2: "winter",
        3: "spring",
        4: "spring",
        5: "spring",
        6: "summer",
        7: "summer",
        8: "summer",
        9: "autumn",
        10: "autumn",
        11: "autumn",
        12: "winter"
    })

    #----- Weather data -------------------------------
    # Coordinates of Karlsruhe
    latitude = 49.014920
    longitude = 8.390050

    start_date = df["date_time"].min().strftime("%Y-%m-%d")
    end_date = df["date_time"].max().strftime("%Y-%m-%d")

    print("Getting weather data...")
    df_weather = utils.weather.get_weather_with_api(latitude=latitude, longitude=longitude, start_date=start_date, end_date=end_date)
    df = pd.merge(df, df_weather, on=["date", "hour"], how="left")

    #----- Remove unnecessary columns -----------------
    # Remove unneeded columns
    df = df.drop(columns=[
        "device_id", 
        "vis", 
        "IR", 
        "WIFI", 
        "BLE", 
        "rssi", 
        "channel_rssi", 
        "snr", 
        "gateway", 
        "channel_index", 
        "spreading_factor", 
        "bandwidth", 
        "f_cnt"])
    
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
    

    working_dir = utils.dirs.set_working_dir()
    if data_dir is None:
        data_dir = os.path.join(working_dir, "data")
    if output_fpath is None:
        output_fpath = os.path.join(working_dir, "data/processed/data_building_n.parquet")

    df = load_data(f"{data_dir}/hka-aqm-n")
    df_preprocessed = preprocess_data(df)
    df_features = add_features(df_preprocessed)
    save_data(df_features, output_fpath)
    return True

def pipeline_from_df(df):
    """
    A function that performs a data pipeline process.

    Args:
        df (pandas.DataFrame): The input DataFrame containing the data.

    Returns:
        pandas.DataFrame: The processed DataFrame with added features.

    """
    df_preprocessed = preprocess_data(df)
    df_features = add_features(df_preprocessed)
    df_features = df_features.sort_values(by="date_time")
    return df_features

# Hauptausführung
if __name__ == "__main__":
    # Set the working directory to the root of the Git repository

    print(pipeline())

    
