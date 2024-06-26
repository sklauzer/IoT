import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Gebäude N Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

data = pd.read_csv("data/processed/data_building_n.csv")

# --------------------------Sidebar Filter ------------------------

# Filter für Floor
st.sidebar.title("Filter nach Floor")
floors = ['floor_0', 'floor_1', 'floor_2', 'floor_3']
selected_floors = st.sidebar.multiselect('Floors', floors, floors)

if selected_floors:
    data = data[data[selected_floors].any(axis=1)]

# Filter für Season
st.sidebar.title("Filter nach Season")
seasons = ['season_autumn', 'season_winter', 'season_spring', 'season_summer']
selected_seasons = st.sidebar.multiselect('Seasons', seasons, seasons)

if selected_seasons:
    data = data[data[selected_seasons].any(axis=1)]

# Filter für Wochentag (day_of_week)
st.sidebar.title("Filter nach Wochentag")
days_of_week_mapping = {
    1: 'Montag',
    2: 'Dienstag',
    3: 'Mittwoch',
    4: 'Donnerstag',
    5: 'Freitag',
    6: 'Samstag',
    7: 'Sonntag'
}
days_of_week = list(range(1, 8))
selected_days_of_week = st.sidebar.multiselect('Wochentage auswählen', [days_of_week_mapping[d] for d in days_of_week], [days_of_week_mapping[d] for d in days_of_week])

if selected_days_of_week:
    selected_days_of_week_indices = [k for k, v in days_of_week_mapping.items() if v in selected_days_of_week]
    data = data[data['day_of_week'].isin(selected_days_of_week_indices)]


#---------------------- Metrik berechnen ------------------------------------------

all_metrics = ['tmp', 'outside_tmp', 'hum', 'outside_hum', 'CO2', 'VOC', 'outside_rain', 'outside_snowfall', 'outside_wind_speed', 'outside_pressure']
inside_metrics = [m for m in all_metrics if not m.startswith('outside_')]
selected_metrics = st.sidebar.multiselect('Werte zur Durchschnittsberechnung (innerhalb)', inside_metrics, inside_metrics)

# Mindestens eine Metrik wählen
if len(selected_metrics) > 0:
    st.subheader('Vergleich der ausgewählten Metriken')

    # Grafiken erstellen
    for metric in selected_metrics:

        # Tagesverlauf
        avg_metrics_per_hour = data.groupby('hour')[metric].mean().reset_index()

        line_chart_hourly = alt.Chart(avg_metrics_per_hour).mark_line().encode(
            x='hour:N',
            y=alt.Y(f'mean({metric}):Q', title=f'Durchschnittlicher {metric}'),
            tooltip=['hour:N', alt.Tooltip(f'mean({metric}):Q', title=f'Durchschnittlicher {metric}')]
        ).properties(
            title=f'Durchschnittlicher {metric} nach Stunde',
            width=600,
            height=400
        )

        st.altair_chart(line_chart_hourly)

        # Gesamtverlauf
    avg_metrics_total = data.groupby('date')[selected_metrics].mean().reset_index()

    for metric in selected_metrics:
        line_chart_total = alt.Chart(avg_metrics_total).mark_line().encode(
            x='date:T',
            y=alt.Y(f'mean({metric}):Q', title=f'Durchschnittlicher {metric}'),
            tooltip=['date:T', alt.Tooltip(f'mean({metric}):Q', title=f'Durchschnittlicher {metric}')]
        ).properties(
            title=f'Durchschnittlicher {metric} über den Gesamtzeitraum',
            width=800,
            height=400
        )

        st.altair_chart(line_chart_total)

else:
    st.write("Bitte wähle mindestens eine Metrik für die Durchschnittsberechnung aus.")



#streamlit run dashboard.py