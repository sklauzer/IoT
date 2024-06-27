import datetime
import os
import sys
import subprocess

current_dir = os.getcwd()
git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=current_dir)
git_root = git_root.decode("utf-8").strip()
os.chdir(git_root)
sys.path.append(git_root)

import streamlit as st
import pandas as pd
import numpy as np


import utils.dashboard

st.set_page_config(
    page_title="Dashboard", 
    layout="centered", 
    initial_sidebar_state="collapsed",

)

df = pd.read_parquet("data/processed/data_building_n.parquet")
rooms = sorted(df["room"].unique())

room_info = pd.read_parquet("data/processed/room_information.parquet")


with st.container(border=True):
    date_col, _, _, room_col = st.columns([1, 1, 1, 1])
    with date_col:
        simulation_date = st.date_input("Simulation Date", value=pd.Timestamp("2022-09-23"))
        simulation_date = pd.Timestamp(simulation_date)
    with room_col:
        room = st.selectbox("Room", rooms)
        df_room = df[(df["room"]==room) & (df["date_time"] <= simulation_date)]
        df_room = df_room.sort_values("date_time", ascending=False)
        room_info = room_info[(room_info["room"]==room) & (room_info["building"] == "N")]
    st.markdown('<hr>', unsafe_allow_html=True)

    #===== Room Status ==============================================================================================
  
    st.markdown(f"<h1 style='margin-top:-30px; margin-bottom:0px; padding-bottom:0'>{room}</h1>", unsafe_allow_html=True)

    if not room_info.empty:
        room_name = room_info["longName"].values[0]
        room_departments = room_info[(room_info["room"]==room) & (room_info["building"] == "N")]["departmentNames"].values[0]
        room_type = room_info[(room_info["room"]==room) & (room_info["building"] == "N")]["roomType"].values[0]

    
        st.markdown(f"<b style='color:#4A55A2;font-size:1.2em;'>{room_name}</b>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            with st.container(border=True):
                st.metric("Room Type", room_type)
                
        with col2:
            if len(room_departments) > 1:
                room_departments = ", ".join(room_departments)
                dep_desc = "Departments"
            else:
                dep_desc = "Department"
                room_departments = room_departments[0]

                with st.container(border=True):
                    st.metric(dep_desc, room_departments)
        
    

        with col3:
            with st.container(border=True):
                icon_col, status_col = st.columns([1, 5], vertical_alignment="top")
                time_diff = simulation_date - df_room["date_time"].max()
                if time_diff <= pd.Timedelta(days=1):
                    status = "Good"
                    icon_path = "Dashboard/assets/good.png"
                elif pd.Timedelta(days=1) < time_diff <= pd.Timedelta(days=2):
                    status = "Warning"
                    icon_path = "Dashboard/assets/warning.png"
                else:
                    status = "Critical"
                    icon_path = "Dashboard/assets/critical.png"

                with icon_col:
                    st.image(icon_path)
                
                with status_col:
                    st.markdown(f"<b>{status}</b>", unsafe_allow_html=True)
                    #st.markdown(f"<left><h4>{status}</h4></left>", unsafe_allow_html=True)

                if time_diff.days == 0:
                    st.markdown(f"Last updated today")
                else:
                    st.markdown(f"Last updated {time_diff.days} days ago")



#===== Metrics ==============================================================================================
# Metrics over the last 24 hours
tmp_max = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["tmp"].max(), 2)
tmp_min = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["tmp"].min(), 2)
tmp_mean = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["tmp"].mean(), 2)
tmp_mean_before = round(df_room[(df_room["date_time"] >= simulation_date - datetime.timedelta(days=2)) & (df_room["date_time"] <= simulation_date - datetime.timedelta(days=1))]["tmp"].mean(), 2)

co2_max = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["CO2"].max(), 2)
co2_min = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["CO2"].min(), 2)
co2_mean = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["CO2"].mean(), 2)
co2_mean_before = round(df_room[(df_room["date_time"] >= simulation_date - datetime.timedelta(days=2)) & (df_room["date_time"] <= simulation_date - datetime.timedelta(days=1))]["CO2"].mean(), 2)

hum_max = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["hum"].max(), 2)
hum_min = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["hum"].min(), 2)
hum_mean = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["hum"].mean(), 2)
hum_mean_before = round(df_room[(df_room["date_time"] >= simulation_date - datetime.timedelta(days=2)) & (df_room["date_time"] <= simulation_date - datetime.timedelta(days=1))]["hum"].mean(), 2)

voc_max = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["VOC"].max(), 2)
voc_min = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["VOC"].min(), 2)
voc_mean = round(df_room[df_room["date_time"] >= simulation_date - datetime.timedelta(days=1)]["VOC"].mean(), 2)
voc_mean_before = round(df_room[(df_room["date_time"] >= simulation_date - datetime.timedelta(days=2)) & (df_room["date_time"] <= simulation_date - datetime.timedelta(days=1))]["VOC"].mean(), 2)

left_metrics, right_metrics = st.columns([1, 1])
with left_metrics:
    with st.container(border=True):
        _, icon_col, _, metric_col = st.columns([1, 3, 1, 10], vertical_alignment="center")
        with icon_col:
            st.image("Dashboard/assets/thermometer.png")
        with metric_col:
            if np.isnan(tmp_mean):
                st.metric(f"Temperature (last 24h)", "No Data")
            else: 
                st.metric(f"Temperature (last 24h)", f"{tmp_mean}°C", delta=f"{round(tmp_mean - tmp_mean_before, 2)}°C")
   
    with st.container(border=True):
        _, icon_col, _, metric_col = st.columns([1, 3, 1, 10], vertical_alignment="center")
        with icon_col:
            st.image("Dashboard/assets/carbon-dioxide.png")
        with metric_col:
            if np.isnan(co2_mean):
                st.metric(f"Temperature (last 24h)", "No Data")
            else: 
                st.metric(f"CO2 (last 24h)", f"{co2_mean} ppm", delta=f"{round(co2_mean - co2_mean_before, 2)} ppm", delta_color="inverse")
       
with right_metrics:
    with st.container(border=True):
        _, icon_col, _, metric_col = st.columns([1, 3, 1, 10], vertical_alignment="center")
        with icon_col:
            st.image("Dashboard/assets/drop.png")
        with metric_col:
            if np.isnan(hum_mean):
                st.metric(f"Temperature (last 24h)", "No Data")
            else: 
                st.metric(f"Humidity (last 24h)", f"{hum_mean} %", delta=f"{round(hum_mean - hum_mean_before, 2)} %")
        # with change_col:
        #     st.markdown(f"<b>Min</b> <br>{hum_min} % <br><b>Max</b> <br>{hum_max} %", unsafe_allow_html=True)

    with st.container(border=True):
        _, icon_col, _, metric_col = st.columns([1, 3, 1, 10], vertical_alignment="center")
        with icon_col:
            st.image("Dashboard/assets/air-pollution.png")
        with metric_col:
            if np.isnan(voc_mean):
                st.metric(f"Temperature (last 24h)", "No Data")
            else: 
                st.metric(f"VOC (last 24h)", f"{voc_mean} ppb", delta=f"{round(voc_mean - voc_mean_before, 2)} ppb", delta_color="inverse")
        

#===== Plot ==============================================================================================
with st.container(border=True):
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        search_start = st.date_input(label="Start Date", key="search_start", value=pd.to_datetime("2022-09-17 00:00:00"))
        search_start = pd.Timestamp(search_start)
    with col2:
        search_end = st.date_input(label="Start Date", key="search_end", value=pd.to_datetime("2022-09-23 23:59:59"))
        search_end = pd.Timestamp(search_end)
    
    with col3:
        sensor_selected = st.radio("Sensor", ["Temperature", "Humidity", "CO2", "VOC"], horizontal=True)
        if sensor_selected == "Temperature":
            sensor_selected = "tmp"
        elif sensor_selected == "Humidity":
            sensor_selected = "hum"
        
    fig = utils.dashboard.get_main_fig(df_room, search_start, search_end, sensor_selected)
    st.plotly_chart(fig, use_container_width=True)


#===== Tachos ==============================================================================================
left_metrics, right_metrics = st.columns([1, 1])
with left_metrics:
    with st.container(border=True):
        st.markdown("<center><h3 style='margin-bottom:-20px'>Temperature (in °C)</h3></center>", unsafe_allow_html=True)
        fig, percentile = utils.dashboard.get_tacho(df, room, "tmp", "rgb(74, 85, 162)", "rgb(197, 223, 248)")
        st.plotly_chart(fig, use_container_width=True)
        if percentile < 50:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average temperature for this room is lower than in <b>{100-percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average temperature for this room is higher than in <b>{percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<center><h3 style='margin-bottom:-20px'>CO2 (in ppm)</h3></center>", unsafe_allow_html=True)
        fig, percentile = utils.dashboard.get_tacho(df, room, "CO2", "rgb(74, 85, 162)", "rgb(197, 223, 248)")
        st.plotly_chart(fig, use_container_width=True)
        if percentile < 50:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average CO2 concentration for this room is lower than in <b>{100-percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average CO2 concentration for this room is higher than in <b>{percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
      
 
with right_metrics:
    with st.container(border=True):
        st.markdown("<center><h3 style='margin-bottom:-20px'>Humidity (in %)</h3></center>", unsafe_allow_html=True)
        fig, percentile = utils.dashboard.get_tacho(df, room, "hum", "rgb(74, 85, 162)", "rgb(197, 223, 248)")
        st.plotly_chart(fig, use_container_width=True)
        if percentile < 50:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average humidity for this room is lower than in <b>{100-percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average humidity for this room is higher than in <b>{percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<center><h3 style='margin-bottom:-20px'>VOC (in ppb)</h3></center>", unsafe_allow_html=True)
        fig, percentile = utils.dashboard.get_tacho(df, room, "VOC", "rgb(74, 85, 162)", "rgb(197, 223, 248)")
        st.plotly_chart(fig, use_container_width=True)
        if percentile < 50:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average VOC concentration for this room is lower than in <b>{100-percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='margin-top:-50px; text-align: center;'>The average VOC concentration for this room is higher than in <b>{percentile} %</b> of all rooms.</p>", unsafe_allow_html=True)
        