import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    layout="wide",
)


file = st.file_uploader("Upload your Strava 'activities.csv' file")

if file:
    df = pd.read_csv(file)

    days_of_week = {0: "Monday", 1: "Tuesday", 2: "Wednesday",
                    3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    df["Activity Date"] = pd.to_datetime(df["Activity Date"]).dt.tz_localize(
        'UTC').dt.tz_convert('Europe/Warsaw')
    df = df.dropna(axis=1, how="all")
    df_clean = (df[["Activity ID", "Activity Date", "Activity Type", "Elapsed Time", "Max Heart Rate", "Average Heart Rate", "Commute"]]
                .query("`Activity Type` not in ['Walk','Workout','Weight Training'] and Commute == False"))
    df_weeks = df_clean.copy()
    df_weeks["DayOfWeek"] = df_weeks["Activity Date"].dt.day_of_week
    df_weeks["Minute"] = df_weeks["Activity Date"].dt.hour * \
        60 + df_weeks["Activity Date"].dt.minute

    minutes_in_day = np.arange(60*24)
    minutes_named = pd.date_range(
        "00:00", "23:59", freq="1min").strftime('%H:%M')
    activity_starts = df_weeks["Minute"].values[:, None]
    activity_ends = activity_starts + \
        (df_weeks["Elapsed Time"]/60).values[:, None]
    activity_mask = (minutes_in_day >= activity_starts) & (
        minutes_in_day <= activity_ends).astype(int)
    activity_heatmap = (pd.DataFrame(activity_mask, index=df_weeks["Activity ID"], columns=minutes_named)
                        .reset_index()
                        .merge(df_weeks[["Activity ID", "DayOfWeek"]], left_on="Activity ID", right_on="Activity ID")
                        .drop(columns="Activity ID")
                        .groupby("DayOfWeek").sum()
                        .rename(index=days_of_week)
                        .fillna(0))

    activity_sum = activity_heatmap.sum()
    active_minutes = activity_sum.to_numpy().nonzero()[0]
    margin = 30
    if len(active_minutes) > 0:
        first_idx = active_minutes[0]
        last_idx = active_minutes[-1]
        start_cut = max(0, first_idx - margin)
        end_cut = min(1440, last_idx + margin)
        heatmap_cropped = activity_heatmap.iloc[:, start_cut:end_cut]

    cols = heatmap_cropped.columns
    tick_labels = [name for name in cols if str(name).endswith(":00")]

    fig = px.imshow(
        heatmap_cropped,
        color_continuous_scale="PuBu",
        aspect="auto"
    )

    fig.update_xaxes(
        tickmode='array',
        tickvals=tick_labels,
        ticktext=tick_labels
    )
    for tick in tick_labels:
        fig.add_vline(
            x=tick,
            line_width=1,
            line_dash="dash",
            line_color="black",
            opacity=0.2
        )

    fig.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    chart = st.plotly_chart(fig)
else:
    st.title("No file loaded yet")
