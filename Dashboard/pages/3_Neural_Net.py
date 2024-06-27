import os
import subprocess
import sys

import numpy as np
import pandas as pd
import streamlit as st
import joblib
import torch
import torch.nn as nn

import utils.nn
from NeuralNetworks.base_class import SimpleLSTM
import utils.data_pipeline

# Set the working directory to the root of the Git repository
def set_git_root_directory():
    current_dir = os.getcwd()
    git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=current_dir)
    git_root = git_root.decode("utf-8").strip()
    os.chdir(git_root)
    sys.path.append(git_root)

set_git_root_directory()

# Set the page title
st.set_page_config(page_title="Neural Net Prediction")
# Set the title
st.title("Neural Net Prediction")

# Description
st.write(
    """This is the application interface of our neural network. 
    This application demonstrates how the model can be used to make 
    a prediction. Six files of a room (consecutive days) are uploaded as input."""
    )

st.markdown("<hr/>", unsafe_allow_html=True)

# Get all models from the NeuralNetworks/models directory
def get_models():
    model_path = 'NeuralNetworks/models'
    return sorted(os.listdir(model_path))

models = get_models()
model_loaded = False

# Let the user select a model
selected_model = st.selectbox("Select a model", models, index=len(models)-1)

# Load the model, x_scaler, y_scaler, and encoder
with st.spinner('Loading model...'):
    model_path = f"NeuralNetworks/models/{selected_model}"
    model = torch.load(f"{model_path}/model.pt")
    x_scaler = joblib.load(f"{model_path}/x_scaler.pkl")
    y_scaler = joblib.load(f"{model_path}/y_scaler.pkl")
    encoder = joblib.load(f"{model_path}/encoder.pkl")
    model_loaded = True

if model_loaded:
    st.write(model)

    # Let the user upload 6 files
    uploaded_files = st.file_uploader("Upload files", type=["csv", "dat"], accept_multiple_files=True)

    # Check the number of uploaded files
    if len(uploaded_files) != 6:
        st.error(f"Please upload 6 files. You have uploaded {len(uploaded_files)} files.")
    else:
        # Load the data
        def load_data(files):
            df_list = []
            for file in files:
                with st.spinner(f"Loading {file.name}..."):
                    df = pd.read_csv(file, sep=";", skiprows=1)
                    df_list.append(df)
            return pd.concat(df_list, ignore_index=True)

        df = load_data(uploaded_files)

        # Preprocess the data
        with st.spinner("Preprocessing data..."):
            df = utils.data_pipeline.pipeline_from_df(df)

        # Check if the data contains only one room
        if len(df['room'].unique()) != 1:
            st.error("The data contains more than one room. Please make sure to upload only data from one room.")
            st.stop()

        room = df['room'].unique()[0]


        # Feature engineering and encoding
        df = utils.nn.feature_engineering(df)
        df = utils.nn.encode(df, encoder)
        df = utils.nn.resample(df)

        # Check if all date_times (index) are consecutive
        df_check_consecutive = df.reset_index()
        df_check_consecutive['date_diff'] = df_check_consecutive['date_time'].diff()
        all_days_following = df_check_consecutive['date_diff'].iloc[1:].eq(pd.Timedelta(days=1)).all()

        if not all_days_following:
            st.error("The data contains non-consecutive days. Please make sure to upload only data with consecutive days.")
            st.stop()

        next_date = df_check_consecutive['date_time'].iloc[-1] + pd.Timedelta(days=1)
        next_date = next_date.strftime("%d.%m.%Y")

        # Make prediction
        X = utils.nn.scaling(df, x_scaler)
        y_pred_scaled = utils.nn.predict(model, X)
        y_pred = utils.nn.rescale(y_pred_scaled, y_scaler)

        st.markdown("<hr/>", unsafe_allow_html=True)

        y_pred = round(y_pred[0], 2)
        st.header("Prediction")
        # 3 columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Room", room)
        col2.metric("Date", next_date)
        col3.metric(f"Predicted Temperature", f"{y_pred:.2f} °C")
