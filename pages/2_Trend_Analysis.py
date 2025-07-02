import streamlit as st
st.set_page_config(page_title="Trend Analysis", layout="wide")  # MUST be first Streamlit command

import pandas as pd
import numpy as np
import plotly.express as px
from utils.db import listeria_collection
import plotly.graph_objects as go
from collections import OrderedDict


# 🔐 Authentication check
if "user" not in st.session_state:
    st.warning("Please log in to access this page.")
    st.stop()

# 👤 Show user info and logout button
st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.user['username']}`")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.success("🔓 Logged out successfully.")
    st.stop()

# Load Data
data = pd.DataFrame(list(listeria_collection.find()))
col1, col2, col3 = st.columns(3)
col1.metric("Total Samples", len(data))
col2.metric("Detected", data[data["test_result"] != "Not Detected"].shape[0])
col3.metric("Detection Rate", f"{(data[data['test_result'] != 'Not Detected'].shape[0] / len(data)) * 100:.2f}%")
#####################################################
# Ensure sample_date is datetime
data['sample_date'] = pd.to_datetime(data['sample_date'])

# Group by day
daily_summary = data.groupby('sample_date')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Create Plotly Figure
fig = go.Figure()

# Total Samples bar
fig.add_trace(go.Bar(
    x=daily_summary['sample_date'],
    y=daily_summary['total_samples'],
    name='Total Samples',
    marker_color='#a06cd5'  # Purple
))

# Detected Samples bar
fig.add_trace(go.Bar(
    x=daily_summary['sample_date'],
    y=daily_summary['detected_tests'],
    name='Detected Samples',
    marker_color='#C00000'  # Red
))

# Layout for grouped bars
fig.update_layout(
    title='Day-wise Total vs Detected Samples',
    xaxis=dict(
        title='Sampling Date',
        type='date',
        tickformat='%d-%b',
        tickangle=-90,
        dtick='D1',
        rangeslider=dict(
        visible=True,
        thickness=0.02,
        bgcolor='lightgrey',
        bordercolor='grey',
        borderwidth=1
    ),
    showgrid=False  # <<< Turn OFF vertical gridlines
    ),
    yaxis=dict(title='Count of Samples'),
    barmode='group',  # Grouped side-by-side bars
    bargap=0.2,
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5
    ),
    height=500,
    margin=dict(l=60, r=40, t=60, b=140)
)

# Show in Streamlit
st.plotly_chart(fig, use_container_width=True, key='daily_total_vs_detected')



#####################################################


# Compute detection stats by week (without categorizing by before_during)
grouped = data.groupby(['week'])

summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (
    (summary['detected_tests'] / summary['total_tests']) * 100
).round(1)

# Extract numeric part of week for proper sorting (e.g., "Week-12" → 12)
summary['week_num'] = summary['week'].str.extract(r'Week-(\d+)').astype(int)

# Sort by the extracted week number
summary = summary.sort_values(by='week_num')

# Fit a linear trend line to detection_rate_percent
x_vals = summary['week_num']
y_vals = summary['detection_rate_percent']

# Fit a 2nd-degree polynomial trend line
coeffs = np.polyfit(x_vals, y_vals, deg=2)
poly = np.poly1d(coeffs)
trend_y = poly(x_vals)


# Create the combo chart
# st.subheader("Detection Summary")

fig = go.Figure()


# Bar for total tests
fig.add_trace(go.Bar(
    x=summary['week'],
    y=summary['total_tests'],
    name='Total Tests',
    marker_color='#dac3e8',
    yaxis='y1'
))

# Line for detection rate %
fig.add_trace(go.Scatter(
    x=summary['week'],
    y=summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    marker=dict(color='#C00000'),
    line=dict(color='#C00000'),
    yaxis='y2'
))


fig.update_layout(
    title="Detection Summary by Week",
    yaxis=dict(
        title="Total/Detected Tests",
        side="left",
        range=[0, 500]
    ),
    yaxis2=dict(
        title="Detection Rate (%)",
        overlaying="y",
        side="right",
        range=[0, 100]
    ),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5
    ),
    # legend=dict(x=0.2, xanchor="center", orientation="h"),
    height=500,
    bargap=0.3,        # Gap between weeks (x categories)
    bargroupgap=0      # No gap between bars in the same group (Total vs Detected)
)

st.plotly_chart(fig, use_container_width=True)

################################################
# Ensure sample_date is datetime
data['sample_date'] = pd.to_datetime(data['sample_date'])

# Group by actual sample_date (daily)
grouped = data.groupby('sample_date')

summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (
    (summary['detected_tests'] / summary['total_tests']) * 100
).round(1)

# Sort by date for plotting
summary = summary.sort_values(by='sample_date')

# Fit a 2nd-degree polynomial trend line
x_vals = summary['sample_date'].map(pd.Timestamp.toordinal)
y_vals = summary['detection_rate_percent']
coeffs = np.polyfit(x_vals, y_vals, deg=2)
poly = np.poly1d(coeffs)
trend_y = poly(x_vals)

# Plot combo chart
# st.subheader("Detection Summary by Date")

fig = go.Figure()

# Total tests (bar)
fig.add_trace(go.Bar(
    x=summary['sample_date'],
    y=summary['total_tests'],
    name='Total Tests',
    marker_color='#a06cd5',
    yaxis='y1',
    opacity=0.6
))

# Detection rate (line)
fig.add_trace(go.Scatter(
    x=summary['sample_date'],
    y=summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    marker=dict(color='#C00000'),
    line=dict(color='#C00000'),
    yaxis='y2'
))

# Layout
fig.update_layout(
    title="Detection Summary by Date",

    xaxis=dict(
    title='Sampling Date',
    type='date',
    tickangle=-90,
    tickformat='%d-%b',
    dtick='D1',
    rangeslider=dict(
        visible=True,
        thickness=0.02,
        bgcolor='lightgrey',
        bordercolor='grey',
        borderwidth=1
    ),
    showgrid=False
    ),
    yaxis=dict(title='Total Tests', side='left', range=[0, 200]),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=0.9,
        xanchor='center',
        x=0.5
    ),
    margin=dict(l=60, r=40, t=80, b=180),
    height=600,
    bargap=0.2,
    bargroupgap=0,
    barmode='overlay'  # Prevent bar grouping
)

st.plotly_chart(fig, use_container_width=True, key='detection_summary_trend')

###############################################




area_summary = data.groupby('sub_area')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()


area_summary['detection_rate_percent'] = (
    (area_summary['detected_tests'] / area_summary['total_samples']) * 100
).round(1)


custom_order = [
    # Fresh
    'PRODUCTION', 'DEBONING', 'DESKINNING', 'INJECTOR',
    'WASHER', 
    # Smoking + Packing
    'ENTRANCE', 'LKPW1', 'LKPW2', 'CFS',
    'OTHER'
    # # Unmapped
    # 'Unmapped'
]
custom_order = list(OrderedDict.fromkeys(custom_order))
area_summary['sub_area'] = pd.Categorical(
    area_summary['sub_area'], 
    categories=custom_order, 
    ordered=True
)
area_summary = area_summary.sort_values('sub_area')
fig = go.Figure()
fig.add_trace(go.Bar(
    x=area_summary['sub_area'],
    y=area_summary['total_samples'],
    name='Total Samples',
    marker_color='#d2b7e5',
    yaxis='y1'
))
fig.add_trace(go.Scatter(
    x=area_summary['sub_area'],
    y=area_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers+text',
    text=area_summary['detection_rate_percent'],
    textposition='top center',
    yaxis='y2',
    line=dict(color='crimson', width=3)
))
fig.update_layout(
    title='# Samples vs % Detection Rate by Area (Process Flow)',
    xaxis=dict(
        title='Sub Area',
        categoryorder='array',
        categoryarray=custom_order
    ),
    yaxis=dict(title='Total Samples', side='left', showgrid=False, range=[0, 500]),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    # legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5
    ),
    height=500
)
st.plotly_chart(fig, use_container_width=True, key="samples_vs_detection_rate")




# 3 Filter for 'Fresh Fish Department' 'Before Production'
# filtered = data[data['before_during'] == 'BP']
filtered = data[
    (data['before_during'] == 'BP') &
    (data['fresh_smoked'] == 'Fresh')
]

# Ensure date column is datetime
filtered['sample_date'] = pd.to_datetime(filtered['sample_date'])

# Group by Date
date_summary = filtered.groupby('sample_date')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Calculate detection rate
date_summary['detection_rate_percent'] = (
    (date_summary['detected_tests'] / date_summary['total_samples']) * 100
).round(1)

# Sort by date
date_summary = date_summary.sort_values(by='sample_date')

# Create chart
fig = go.Figure()

# Bar for total samples
fig.add_trace(go.Bar(
    x=date_summary['sample_date'],
    y=date_summary['total_samples'],
    name='Total Samples',
    marker_color='#a06cd5',
    yaxis='y1'
))

# Line for detection rate
fig.add_trace(go.Scatter(
    x=date_summary['sample_date'],
    y=date_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    line=dict(color='crimson', width=2),
    yaxis='y2'
))

# Layout with top legend and all date ticks
fig.update_layout(
    title='# Samples vs Detection Rate for Fresh Department Before Production',
    xaxis=dict(
        title='Sampling Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',  # e.g., 12-May
        dtick='D1',          # Force daily tick labels
        rangeslider=dict(
            visible=True,
            thickness=0.02,
            bgcolor='lightgrey',
            bordercolor='grey',
            borderwidth=1
        ),
        showgrid=False
    ),
    yaxis=dict(title='Total Samples', side='left', range=[0, 100]),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=0.9,  # Above chart
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='before_production_trend')

# 4 Filter for 'Fresh Fish Department' 'During Production'

filtered = data[
    (data['before_during'] == 'DP') &
    (data['fresh_smoked'] == 'Fresh')
]
# Ensure date column is datetime
filtered['sample_date'] = pd.to_datetime(filtered['sample_date'])

# Group by Date
date_summary = filtered.groupby('sample_date')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Calculate detection rate
date_summary['detection_rate_percent'] = (
    (date_summary['detected_tests'] / date_summary['total_samples']) * 100
).round(1)

# Sort by date
date_summary = date_summary.sort_values(by='sample_date')

# Create chart
fig = go.Figure()

# Bar for total samples
fig.add_trace(go.Bar(
    x=date_summary['sample_date'],
    y=date_summary['total_samples'],
    name='Total Samples',
    marker_color='#a06cd5',
    yaxis='y1'
))

# Line for detection rate
fig.add_trace(go.Scatter(
    x=date_summary['sample_date'],
    y=date_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    line=dict(color='crimson', width=2),
    yaxis='y2'
))

# Layout with top legend and all date ticks
fig.update_layout(
    title='# Samples vs Detection Rate for Fresh Department During Production',
    xaxis=dict(
        title='Sampling Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',  # e.g., 12-May
        dtick='D1',          # Force daily tick labels
        rangeslider=dict(
            visible=True,
            thickness=0.02,
            bgcolor='lightgrey',
            bordercolor='grey',
            borderwidth=1
        ),
        showgrid=False
    ),
    yaxis=dict(title='Total Samples', side='left', range=[0, 100]),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=0.9,  # Above chart
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='during_production_trend')
#############################################################################

# 5 Filter for 'Fresh Fish Department' 'Before Production'
# filtered = data[data['before_during'] == 'BP']
filtered = data[
    (data['before_during'] == 'BP') &
    (data['fresh_smoked'] == 'Smoking + Packing')
]

# Ensure date column is datetime
filtered['sample_date'] = pd.to_datetime(filtered['sample_date'])

# Group by Date
date_summary = filtered.groupby('sample_date')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Calculate detection rate
date_summary['detection_rate_percent'] = (
    (date_summary['detected_tests'] / date_summary['total_samples']) * 100
).round(1)

# Sort by date
date_summary = date_summary.sort_values(by='sample_date')

# Create chart
fig = go.Figure()

# Bar for total samples
fig.add_trace(go.Bar(
    x=date_summary['sample_date'],
    y=date_summary['total_samples'],
    name='Total Samples',
    marker_color='#ff8503',  
    # #a06cd5
    yaxis='y1'
))

# Line for detection rate
fig.add_trace(go.Scatter(
    x=date_summary['sample_date'],
    y=date_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    line=dict(color='crimson', width=2),
    yaxis='y2'
))

# Layout with top legend and all date ticks
fig.update_layout(
    title='# Samples vs Detection Rate for Smoked Department Before Production',
    xaxis=dict(
        title='Sampling Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',  # e.g., 12-May
        dtick='D1',          # Force daily tick labels
        rangeslider=dict(
            visible=True,
            thickness=0.02,
            bgcolor='lightgrey',
            bordercolor='grey',
            borderwidth=1
        ),
        showgrid=False
    ),
    yaxis=dict(title='Total Samples', side='left', range=[0, 100]),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=0.9,  # Above chart
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='before_production_smoked_trend')

# 6 Filter for 'Fresh Fish Department' 'During Production'

filtered = data[
    (data['before_during'] == 'DP') &
    (data['fresh_smoked'] == 'Smoking + Packing')
]
# Ensure date column is datetime
filtered['sample_date'] = pd.to_datetime(filtered['sample_date'])

# Group by Date
date_summary = filtered.groupby('sample_date')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Calculate detection rate
date_summary['detection_rate_percent'] = (
    (date_summary['detected_tests'] / date_summary['total_samples']) * 100
).round(1)

# Sort by date
date_summary = date_summary.sort_values(by='sample_date')

# Create chart
fig = go.Figure()

# Bar for total samples
fig.add_trace(go.Bar(
    x=date_summary['sample_date'],
    y=date_summary['total_samples'],
    name='Total Samples',
    marker_color='#ff8503',
    yaxis='y1'
))

# Line for detection rate
fig.add_trace(go.Scatter(
    x=date_summary['sample_date'],
    y=date_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    line=dict(color='crimson', width=2),
    yaxis='y2'
))

# Layout with top legend and all date ticks
fig.update_layout(
    title='# Samples vs Detection Rate for Smoked Department During Production',
    xaxis=dict(
        title='Sampling Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',  # e.g., 12-May
        dtick='D1',          # Force daily tick labels
        rangeslider=dict(
            visible=True,
            thickness=0.02,
            bgcolor='lightgrey',
            bordercolor='grey',
            borderwidth=1
        ),
        showgrid=False
    ),
    yaxis=dict(title='Total Samples', side='left', range=[0, 100]),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=0.9,  # Above chart
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='during_production_Smoked_trend')




###############################################################
# --- Map sub_area to departments ---
fresh_areas = ['PRODUCTION', 'DEBONING', 'DESKINNING', 'INJECTOR', 'WASHER']
smoking_packing_areas = ['ENTRANCE', 'LKPW1', 'LKPW2', 'CFS', 'OTHER']

# Assign department based on sub_area
def assign_department(area):
    if area in fresh_areas:
        return 'Fresh'
    elif area in smoking_packing_areas:
        return 'Smoking + Packing'
    else:
        return 'Unmapped'

data['department'] = data['sub_area'].apply(assign_department)

# --- Filter for valid departments only ---
data = data[data['department'].isin(['Fresh', 'Smoking + Packing'])]

# --- Ensure sample_date is datetime ---
data['sample_date'] = pd.to_datetime(data['sample_date'])

# --- Group by sample_date and department ---
grouped = data.groupby(['sample_date', 'department'])['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# --- Calculate detection rate ---
grouped['detection_rate_percent'] = (
    (grouped['detected_tests'] / grouped['total_samples']) * 100
).round(1)

# --- Pivot for Plotly line chart ---
pivot = grouped.pivot(index='sample_date', columns='department', values='detection_rate_percent').fillna(0)

# --- Plotting ---
fig = go.Figure()

colors = {
    'Fresh': '#C00000',             # crimson
    'Smoking + Packing': '#FF8503'  # Dark Orange
}

for dept in pivot.columns:
    fig.add_trace(go.Scatter(
        x=pivot.index,
        y=pivot[dept],
        name=f'{dept} Detection Rate (%)',
        mode='lines+markers',
        line=dict(color=colors[dept], width=2),
        marker=dict(size=6)
    ))

# --- Layout ---
fig.update_layout(
    title="Detection Rate Trend by Department",
    
    xaxis=dict(
        title='Sampling Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',
        dtick='D1',
        # rangeslider=dict(visible=True),
        #  thickness=0.01  # 1% of plot height
        # showgrid=True
        rangeslider=dict(
        visible=True,
        thickness=0.02,
        bgcolor='lightgrey',
        bordercolor='grey',
        borderwidth=1
    ),
    showgrid=False
    ),
    yaxis=dict(title='Detection Rate (%)', range=[0, 120]),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=0.9,
        xanchor='center',
        x=0.5
    ),
    height=500,
    margin=dict(l=60, r=40, t=80, b=120)
)

# --- Display in Streamlit ---
st.plotly_chart(fig, use_container_width=True, key='department_trend')
