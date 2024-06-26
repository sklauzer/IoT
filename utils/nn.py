import os
import subprocess

# Set the working directory to the root of the Git repository
current_dir = os.getcwd()
git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=current_dir)
git_root = git_root.decode("utf-8").strip()
os.chdir(git_root)
cwd = os.getcwd()

import math
from datetime import date
import calendar

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import KBinsDiscretizer, MinMaxScaler, OneHotEncoder

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

import joblib

def project_date_to_unit_circle(input_date: date):
    """ Projects a date to a unit circle. """
    year = input_date.year
    passed_days = (input_date - date(year, 1, 1)).days + 1
    nr_of_days_per_year = 366 if calendar.isleap(year) else 365
    position_within_year = passed_days / nr_of_days_per_year
    alpha = position_within_year * math.pi * 2
    year_circle_x = (math.sin(alpha) + 1) / 2
    year_circle_y = (math.cos(alpha) + 1) / 2
    return year_circle_x, year_circle_y

def project_day_of_week_to_unit_circle(input_day_of_week: int):
    """ Projects a day of the week to a unit circle. """
    alpha = input_day_of_week / 7 * math.pi * 2
    day_of_week_circle_x = (math.sin(alpha) + 1) / 2
    day_of_week_circle_y = (math.cos(alpha) + 1) / 2
    return day_of_week_circle_x, day_of_week_circle_y

def create_sequences(data, features, sequence_length):
    sequences = []
    targets = []
    
    for room in data['room'].unique():
        df_room = data[data['room'] == room].reset_index()
        for i in range(len(df_room) - sequence_length):
            # Prüfe, ob die Tage aufeinanderfolgend sind
            if (df_room.loc[i + sequence_length - 1, 'date_time'] - df_room.loc[i, 'date_time']).days == sequence_length - 1:
                sequences.append(df_room.loc[i:i+sequence_length-2, features].drop(columns=['room']).values)
                targets.append(df_room.loc[i + sequence_length -1, 'tmp'])
    
    return np.array(sequences), np.array(targets)


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """ Feature Engineering for the neural network. """
    # Project the date to a unit circle (year)
    df['date_circle_x'], df['date_circle_y'] = zip(*df['date'].apply(project_date_to_unit_circle))

    # Project the day_of_week to a unit circle (week)
    df['day_of_week_circle_x'], df['day_of_week_circle_y'] = zip(*df['day_of_week'].apply(project_day_of_week_to_unit_circle))

    return df

def encode(df: pd.DataFrame, encoder: OneHotEncoder) -> pd.DataFrame:
    """ One-Hot-Encoding for the neural network. """
    encoded_columns = encoder.transform(df[['season', 'floor']])

    # Generate the column names for the one-hot-encoded columns
    encoded_column_names = encoder.get_feature_names_out(['season', 'floor'])

    # Insert the one-hot-encoded columns into the DataFrame
    df_encoded = pd.DataFrame(encoded_columns, columns=encoded_column_names)
    df = pd.concat([df, df_encoded], axis=1).drop(['season', 'floor'], axis=1)

    return df
    
def resample(df: pd.DataFrame) -> pd.DataFrame:
    """ Resample the data to daily values. """
    #----- Resampling ----------------------------------------
    df.set_index('date_time', inplace=True)
    df_daily = df.groupby('room').resample('D').mean().dropna()

    df_daily.reset_index(inplace=True)
    df_daily.set_index(['date_time'], inplace=True)

    #----- Remove unnecessary columns -------------------------
    df_daily = df_daily[[
        'tmp', 'hum', 'CO2', 'VOC', 'outside_tmp', 'outside_hum', 'outside_rain',
        'outside_snowfall', 'outside_wind_speed', 'outside_pressure',
        'date_circle_x', 'date_circle_y', 'day_of_week_circle_x',
        'day_of_week_circle_y', 'season_autumn', 'season_spring',
        'season_summer', 'season_winter', 'floor_0', 'floor_1', 'floor_2',
        'floor_3'
        ]]
    
    return df_daily


def scaling(df:pd.DataFrame, x_scaler:MinMaxScaler) -> np.array:
    """ Scale the data """
    X = df.values
    n_samples, n_features = X.shape
    X_reshaped = X.reshape(-1, n_features)

    X_scaled = x_scaler.transform(X_reshaped).reshape(n_samples, n_features)
    return X_scaled

def predict(model: nn.Module, X: np.array) -> np.array:
    """ Predict the target value. """
    if torch.cuda.is_available():
        device = torch.device('cuda')
    elif torch.backends.mps.is_available():
        device = torch.device('mps')
    else:
        device = torch.device('cpu')

    X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(0).to(device)
    
    model.eval()
    with torch.no_grad():
        y_pred_scaled = model(X_tensor).squeeze().cpu().numpy()
    
    return y_pred_scaled

def rescale(y_pred_scaled: np.array, y_scaler: MinMaxScaler) -> np.array:
    """ Rescale the predictions. """
    y_pred = y_scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
    return y_pred

