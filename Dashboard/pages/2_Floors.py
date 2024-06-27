import itertools
import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt 

st.set_page_config(
    page_title="Floors",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    /* Hintergrundfarbe für die gesamte Seite */
    .stApp {
    background: rgb(251,253,255);
background: linear-gradient(0deg, rgba(251,253,255,1) 43%, rgba(246,251,255,1) 100%);
    }

    /* Beispiel für benutzerdefinierte Abschnitte */
    .st-emotion-cache-4uzi61 {
        background-color: #ffffff;  /* Hintergrundfarbe für einen bestimmten Abschnitt */
        border-color:#ffffff;
        box-shadow: 0 0 5px rgba(0,0,0,0.1);  /* Schatten für einen bestimmten Abschnitt */
    }

    .st-emotion-cache-12fmjuu{
        background-color: #f6fbff; /* Hintergrundfarbe für einen bestimmten Abschnitt */
          }

    </style>
    """,
    unsafe_allow_html=True
)

data = pd.read_parquet("data/processed/data_building_n.parquet")

data['date'] = pd.to_datetime(data['date'])

# --------------------------Sidebar Filter ------------------------

# Filter für Floor
st.sidebar.title("Filter")
floors = sorted(list(data["floor"].unique()))
selected_floors = st.sidebar.multiselect('Floor', floors)

if selected_floors:
    data = data[data["floor"].isin(selected_floors)]

# Dynamischer Filter für Raum (nur die Räume anzeigen, die zu den ausgewählten Etagen gehören)
if selected_floors:
    rooms_in_selected_floors = data['room'].unique()
    selected_rooms = st.sidebar.multiselect('Room', sorted(rooms_in_selected_floors))

    if selected_rooms:
        data = data[data['room'].isin(selected_rooms)]

# Filter für Season
seasons = data['season'].unique()
selected_seasons = st.sidebar.multiselect('Season', seasons, seasons, format_func=lambda x: x.capitalize())

if selected_seasons:
    data = data[data["season"].isin(selected_seasons)]

# Filter für Wochentag (day_of_week)
days_of_week_mapping = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}

days_of_week = sorted(list(data["day_of_week"].unique()))
selected_days_of_week = st.sidebar.multiselect('Weekday', [days_of_week_mapping[d] for d in days_of_week], [days_of_week_mapping[d] for d in days_of_week])

if selected_days_of_week:
    selected_days_of_week_indices = [k for k, v in days_of_week_mapping.items() if v in selected_days_of_week]
    data = data[data['day_of_week'].isin(selected_days_of_week_indices)]


#---------------------- Metrik berechnen ------------------------------------------

all_metrics = ['tmp', 'outside_tmp', 'hum', 'outside_hum', 'CO2', 'VOC', 'outside_rain', 'outside_snowfall', 'outside_wind_speed', 'outside_pressure']
inside_metrics = [m for m in all_metrics if not m.startswith('outside_')]
outside_metrics = [m for m in all_metrics if m.startswith('outside_')]

selected_inside_metrics = st.sidebar.multiselect('Sensor (inside)', inside_metrics, [])
selected_outside_metrics = st.sidebar.multiselect('Weather Data (outside)', outside_metrics, [])

selected_metrics = selected_inside_metrics + selected_outside_metrics

if len(selected_metrics) > 0:
    if len(selected_floors) > 1:
        st.title(f"Floors: {', '.join(selected_floors)}")
    else:
        st.title(f"Floor: {selected_floors[0]}")

    if len(selected_rooms) == 0:
        st.write("All Rooms")

    elif len(selected_rooms) > 1:
        st.write(f"Rooms: {', '.join(selected_rooms)}")
    else:
        st.write(f"Room: {selected_rooms[0]}")

    # Tagesverlauf 
    for metric in selected_metrics:
        with st.container(border=True):
            st.subheader(f'{metric.upper()}')

            avg_metrics_per_hour = data.groupby('hour')[metric].mean().reset_index()
            line_chart_hourly = alt.Chart(avg_metrics_per_hour).mark_line().encode(
                x='hour:N',
                y=alt.Y(f'mean({metric}):Q', title=f'{metric}'),
                tooltip=['hour:N', alt.Tooltip(f'mean({metric}):Q', title=f'Durchschnitt {metric}')]
            ).properties(
                title=f'Mean {metric} during the day',
                width=400,
                height=300
            )

            # Gesamtverlauf
            avg_metrics_total = data.groupby('date')[metric].mean().reset_index()
            
            # Resample on daily basis
            avg_metrics_total = avg_metrics_total.set_index('date').resample('D').mean().reset_index()
            data[metric] = data[metric].where(pd.notnull(data[metric]), None)

            line_chart_total = alt.Chart(avg_metrics_total).mark_line(interpolate='linear').encode(
                x='date:T',
                y=alt.Y(f'mean({metric}):Q', title=f'{metric}'),
                tooltip=['date:T', alt.Tooltip(f'mean({metric}):Q', title=f'{metric}')]
            ).properties(
                title=f'Mean {metric} over the entire period',
                width=400,
                height=300
            )

            col1, col2 = st.columns(2)
            col1.altair_chart(line_chart_hourly)
            col2.altair_chart(line_chart_total)

if len(selected_metrics) > 1:
    st.subheader('Compare Metrics')
    metrica = st.selectbox('Select first metric', set(selected_metrics), key='compare_metric1')
    available_metrics = [metric for metric in selected_metrics if metric != metrica]
    metricb = st.selectbox('Select second metric', available_metrics, key='compare_metric2')

    # Auswahloption für den y-Wert hinzufügen
    comparison_type = st.radio("Select comparison type", ("Daily course", "Overall course"), key='comparison_type')

    def combine_metrics_by_hour(data, metrica, metricb):
        combined_data = data.groupby('hour')[[metrica, metricb]].mean().reset_index()
        base = alt.Chart(combined_data).encode(x='hour:N')

        line1 = base.mark_line(color='blue').encode(
            y=alt.Y(f'{metrica}:Q', axis=alt.Axis(title=f'{metrica}'))
        )

        line2 = base.mark_line(color='red').encode(
            y=alt.Y(f'{metricb}:Q', axis=alt.Axis(title=f'{metricb}', orient='right'))
        )

        chart = alt.layer(line1, line2).resolve_scale(
            y='independent'
        ).properties(
            width=400,
            height=400,
            title=f'Comparison of {metrica.upper()} and {metricb.upper()} on daily course'
        )

        return chart

    def combine_metrics_by_date(data, metrica, metricb):
        combined_data = data[['date', metrica, metricb]].set_index('date').resample('D').mean().reset_index()
        base = alt.Chart(combined_data).encode(x='date:T')

        line1 = base.mark_line(color='blue').encode(
            y=alt.Y(f'{metrica}:Q', axis=alt.Axis(title=f'{metrica}'))
        )

        line2 = base.mark_line(color='red').encode(
            y=alt.Y(f'{metricb}:Q', axis=alt.Axis(title=f'{metricb}', orient='right'))
        )

        chart = alt.layer(line1, line2).resolve_scale(
            y='independent'
        ).properties(
            width=400,
            height=400,
            title=f'Comparison of {metrica} and {metricb} on overall course'
        )

        return chart

    if comparison_type == "Daily course":
        chart_hour = combine_metrics_by_hour(data, metrica, metricb)
        st.altair_chart(chart_hour, use_container_width=True)
    else:
        chart_date = combine_metrics_by_date(data, metrica, metricb)
        st.altair_chart(chart_date, use_container_width=True)


if len(selected_metrics) > 1:
    show_scatterplots = st.checkbox('Show Scatterplots for correlation analysis')

    if show_scatterplots:
        with st.container(border=True):
            st.title('Scatterplots of the selected metrics')
            for metric1, metric2 in itertools.combinations(selected_metrics, 2):
                st.subheader(f"{metric1.upper()} vs. {metric2.upper()}")
                st.write(f"Correlation coefficient: {round(data[metric1].corr(data[metric2]), 3)}")
                scatter_chart = alt.Chart(data).mark_circle().encode(
                    x=metric1,
                    y=metric2,
                    tooltip=[metric1, metric2]
                ).properties(
                    width=400,
                    height=300
                )
                st.altair_chart(scatter_chart)