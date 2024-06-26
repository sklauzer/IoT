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
st.sidebar.title("Filter")
floors = ['floor_0', 'floor_1', 'floor_2', 'floor_3']
selected_floors = st.sidebar.multiselect('Floors', floors, floors)

if selected_floors:
    data = data[data[selected_floors].any(axis=1)]

# Dynamischer Filter für Raum (nur die Räume anzeigen, die zu den ausgewählten Etagen gehören)
if selected_floors:
    rooms_in_selected_floors = data[data[selected_floors].any(axis=1)]['room'].unique()
    selected_rooms = st.sidebar.multiselect('Räume', sorted(rooms_in_selected_floors))

    if selected_rooms:
        data = data[data['room'].isin(selected_rooms)]

# Filter für Season
seasons = ['season_autumn', 'season_winter', 'season_spring', 'season_summer']
selected_seasons = st.sidebar.multiselect('Seasons', seasons, seasons)

if selected_seasons:
    data = data[data[selected_seasons].any(axis=1)]

# Filter für Wochentag (day_of_week)
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
selected_days_of_week = st.sidebar.multiselect('Wochentag', [days_of_week_mapping[d] for d in days_of_week], [days_of_week_mapping[d] for d in days_of_week])

if selected_days_of_week:
    selected_days_of_week_indices = [k for k, v in days_of_week_mapping.items() if v in selected_days_of_week]
    data = data[data['day_of_week'].isin(selected_days_of_week_indices)]


#---------------------- Metrik berechnen ------------------------------------------

all_metrics = ['tmp', 'outside_tmp', 'hum', 'outside_hum', 'CO2', 'VOC', 'outside_rain', 'outside_snowfall', 'outside_wind_speed', 'outside_pressure']
inside_metrics = [m for m in all_metrics if not m.startswith('outside_')]
outside_metrics = [m for m in all_metrics if m.startswith('outside_')]

selected_inside_metrics = st.sidebar.multiselect('Werte (innerhalb)', inside_metrics, [])
selected_outside_metrics = st.sidebar.multiselect('Werte (außerhalb)', outside_metrics, [])

selected_metrics = selected_inside_metrics + selected_outside_metrics

def combine_metrics(data, metric1, metric2, by='hour'):
    combined_data = data.groupby(by)[[metric1, metric2]].mean().reset_index()
    base = alt.Chart(combined_data).encode(x=f'{by}:N')

    line1 = base.mark_line(color='blue').encode(
        y=alt.Y(f'mean({metric1}):Q', axis=alt.Axis(title=f'{metric1}'))
    )

    line2 = base.mark_line(color='red').encode(
        y=alt.Y(f'mean({metric2}):Q', axis=alt.Axis(title=f'{metric2}', orient='right'))
    )

    chart = alt.layer(line1, line2).resolve_scale(
        y='independent'
    ).properties(
        width=600,
        height=400,
        title=f'Vergleich {metric1} und {metric2} nach {by}'
    )

    return chart

if len(selected_metrics) > 0:
    st.subheader('Vergleich der Metriken')

    # Tagesverlauf 
    for metric in selected_metrics:
        st.subheader(f'Durchschnitt {metric}')

        avg_metrics_per_hour = data.groupby('hour')[metric].mean().reset_index()
        line_chart_hourly = alt.Chart(avg_metrics_per_hour).mark_line().encode(
            x='hour:N',
            y=alt.Y(f'mean({metric}):Q', title=f'Durchschnitt {metric}'),
            tooltip=['hour:N', alt.Tooltip(f'mean({metric}):Q', title=f'Durchschnitt {metric}')]
        ).properties(
            title=f'Durchschnitt {metric} im Tagesverlauf',
            width=400,
            height=300
        )

        # Gesamtverlauf
        avg_metrics_total = data.groupby('date')[metric].mean().reset_index()
        line_chart_total = alt.Chart(avg_metrics_total).mark_line().encode(
            x='date:T',
            y=alt.Y(f'mean({metric}):Q', title=f'Durchschnitt {metric}'),
            tooltip=['date:T', alt.Tooltip(f'mean({metric}):Q', title=f'Durchschnitt {metric}')]
        ).properties(
            title=f'Durchschnitt {metric} über den Gesamtzeitraum',
            width=800,
            height=400
        )

        col1, col2 = st.columns(2)
        col1.altair_chart(line_chart_hourly)
        col2.altair_chart(line_chart_total)

show_scatterplots = st.checkbox('Scatterplots anzeigen für Korrelationsanalyse')

if show_scatterplots and len(selected_metrics) > 1:
    st.subheader('Scatterplots der ausgewählten Metriken')
    for metric1 in selected_metrics:
        for metric2 in selected_metrics:
            if metric1 != metric2:
                scatter_chart = alt.Chart(data).mark_circle().encode(
                    x=metric1,
                    y=metric2,
                    tooltip=[metric1, metric2]
                ).properties(
                    width=400,
                    height=400
                )
                st.altair_chart(scatter_chart)
else:
    st.write("Aktiviere die Option 'Scatterplots anzeigen für Korrelationsanalyse' und wähle mindestens zwei Metriken aus, um die Scatterplots zu sehen.")

# Korrelationskoeffizienten zwischen Metriken berechnen
if len(selected_metrics) > 1:
    st.subheader('Korrelationskoeffizient zwischen zwei Metriken')
    metric1 = st.selectbox('Erste Metrik auswählen', selected_metrics)
    metric2 = st.selectbox('Zweite Metrik auswählen', selected_metrics)

    correlation_coefficient = data[metric1].corr(data[metric2])
    st.write(f"Korrelationskoeffizient zwischen {metric1} und {metric2}: {correlation_coefficient}")

