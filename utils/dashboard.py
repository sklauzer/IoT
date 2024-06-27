import pandas as pd
import plotly.graph_objects as go
import datetime

def get_main_fig(df_room, search_start, search_end, sensor_selected):
    """ Create a plotly figure with the given data and parameters """

    #----- Filter Data to only show the selected time range -----------------------------------------------------
    df_data = df_room[(df_room["date_time"] >= search_start) & (df_room["date_time"] <= search_end)]
    df_data = df_data.sort_values("date_time", ascending=True)
    df_data = df_data.set_index("date_time")

    df_data = df_data[[sensor_selected]]
    #----- Resample Data to show the correct time range ---------------------------------------------------------
    time_diff = search_end - search_start

    if time_diff <= datetime.timedelta(days=1):
        date_range = pd.date_range(start=search_start.strftime("%Y-%m-%d %H"), end=search_end.strftime("%Y-%m-%d %H"), freq="H")
        df_data = df_data.resample("H").mean().reindex(date_range)

    elif time_diff > datetime.timedelta(days=1) and time_diff <= datetime.timedelta(days=6):
        date_range = pd.date_range(start=search_start.strftime("%Y-%m-%d %H"), end=search_end.strftime("%Y-%m-%d %H"), freq="H")
        df_data = df_data.resample("H").mean().reindex(date_range)

    elif time_diff > datetime.timedelta(days=6):
        date_range = pd.date_range(start=search_start.date(), end=search_end.date(), freq="D")
        df_data = df_data.resample("D").mean().reindex(date_range)
        
    df_data[sensor_selected] = df_data[sensor_selected].round(2)


    #----- Define Parameters for the Plot ----------------------------------------------------------------------------
    params = {"tmp": {"ticksuffix": "°", "dtick": 2, "yrange": 10, "linecolor": "rgb(74, 85, 162)", "hoverbackground": "rgb(74, 85, 162, 0.5)", "hovercolor": "rgb(255, 255, 255, 1)"},
            "hum": {"ticksuffix": "%", "dtick": 10, "yrange": 30, "linecolor": "rgb(74, 85, 162)", "hoverbackground": "rgb(74, 85, 162, 0.5)", "hovercolor": "rgb(255, 255, 255, 1)"},
            "CO2": {"ticksuffix": " ppm", "dtick": 500, "yrange": 300, "linecolor": "rgb(20, 20, 20, 1)", "hoverbackground": "rgb(100, 100, 100, 1)", "hovercolor": "rgb(255, 255, 255, 1)"},
            "VOC": {"ticksuffix": "ppb", "dtick": 500, "yrange": 300, "linecolor": "rgb(74, 85, 162)", "hoverbackground": "rgb(74, 85, 162, 0.5)", "hovercolor": "rgb(255, 255, 255, 1)"},}

    params_sensor = params.get(sensor_selected)


    #===== Create Plot ==============================================================================================
    fig = go.Figure()

    #----- Add Boxes for different CO2 Levels ------------------------------------------------------------------------
    if sensor_selected == "CO2":
        fig.add_shape(type="rect",
        x0=min(df_data.index), y0=0, x1=max(df_data.index), y1=850,
        fillcolor="green", opacity=0.1, line_width=0)

        fig.add_shape(type="rect",
            x0=min(df_data.index), y0=850, x1=max(df_data.index), y1=1200,
            fillcolor="yellow", opacity=0.1, line_width=0)

        fig.add_shape(type="rect",
            x0=min(df_data.index), y0=1200, x1=max(df_data.index), y1=10000,
            fillcolor="red", opacity=0.1, line_width=0)
    
    #----- Add main line -------------------------------------------------------------------------------------------
    fig.add_trace(go.Scatter(
        x=df_data.index,
        y=df_data[sensor_selected],
        mode='lines',
        line=dict(color=params_sensor.get("linecolor"), width=3),
        name=sensor_selected
    ))

    #----- Define Scale of the Plot ---------------------------------------------------------------------------------
    y_min = df_data[sensor_selected].min(skipna=True)
    y_max = df_data[sensor_selected].max(skipna=True)

    midpoint = (y_min + y_max) / 2
    half_range = max((y_max - y_min) / 2, params_sensor.get("yrange") / 2)

    y_range_min = midpoint - half_range
    y_range_max = midpoint + half_range

    y_range_min = (y_range_min // params_sensor.get("dtick")) * params_sensor.get("dtick")
    y_range_max = ((y_range_max // params_sensor.get("dtick")) + 1) * params_sensor.get("dtick")


    #----- Style the Plot --------------------------------------------------------------------------------------------
    fig.update_layout(
        dragmode=False,
        hovermode='x',
        hoverlabel=dict(
            bgcolor=params_sensor.get("hoverbackground"),
            bordercolor=params_sensor.get("linecolor"),
            font=dict(color=params_sensor.get("hovercolor"))
        ),

        xaxis=dict(
            fixedrange=True,
            showgrid=False,
            showline=True,
            linecolor='rgba(0, 0, 0, 0)',
            linewidth=40,
            tickfont=dict(color='rgba(0, 0, 0, 0.6)'),
            title=""
        ),

        yaxis=dict(
            fixedrange=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            gridwidth=1,
            griddash='dot',
            showgrid=True,
            showline=True,
            linecolor='rgba(0, 0, 0, 0)',
            linewidth=20,
            range=[y_range_min, y_range_max],
            dtick=params_sensor.get("dtick"),
            ticksuffix=params_sensor.get("ticksuffix"),   
            tickfont=dict(color='rgba(0, 0, 0, 0.6)'),
            title=""
        
        ),
            
        plot_bgcolor='white',  # Hintergrundfarbe des Plots
        paper_bgcolor='white',  # Hintergrundfarbe des gesamten Bildes
        width=800,
        height=400,

    )

    return fig



def get_tacho(df, room, sensor, main_color="blue", light_color="lightgrey"):
    room_avg = df.groupby('room')[sensor].mean().reset_index()
    room_avg = room_avg.rename(columns={sensor: f'avg_{sensor}'})
    avg_to_compare = room_avg[room_avg['room'] == room][f'avg_{sensor}'].values[0]
    room_avg['quantile'] = pd.qcut(room_avg[f'avg_{sensor}'], q=100, labels=False, duplicates='drop')

    quantile_of_room = room_avg[room_avg['room'] == room]['quantile'].values[0]
    percentile_of_room = (quantile_of_room + 1)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_to_compare,
        number={'font': {'size': 40}},
        gauge={
            'axis': {'range': [room_avg[f'avg_{sensor}'].min(), room_avg[f'avg_{sensor}'].max()],
                    'tickfont': {'size': 20, 'color': "black"}},
            'bar': {'color': main_color, 'thickness': 0.4},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [room_avg[f'avg_{sensor}'].min(), room_avg[f'avg_{sensor}'].max()], 'color': light_color, 'thickness': 0.4},
            ],
            'threshold': {
                'line': {'color': main_color, 'width': 1},
                'thickness': 0.4,
                'value': avg_to_compare
            }
        },
        
    ))

    fig.update_layout(
        width=300,
        height=300,
        font=dict(size=12),
        margin=dict(l=50, r=50, b=0, t=0),
    )

    return fig, percentile_of_room