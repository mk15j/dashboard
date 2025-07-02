import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
from pymongo import MongoClient
from datetime import datetime, timedelta
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO

# MongoDB connection
client = MongoClient(st.secrets["MONGO_URI"])
db = client["koral"]
listeria_collection = db["listeria"]

def load_image_base64(image_path="koral6_3.png"):
    if not os.path.exists(image_path):
        st.error(f"Image not found at {image_path}")
        return None, None, (0, 0)
    image = Image.open(image_path)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return image, f"data:image/png;base64,{img_str}", image.size  # (width, height)

# ---- Streamlit App ----
st.set_page_config(page_title="Fresh Map", page_icon="🧫", layout="wide")
# st.title("Listeria Sample Map Visualization")

# Load image for background
image_pil, image_base64, (width, height) = load_image_base64()

# Get data with x and y
# all_data = list(listeria_collection.find({"x": {"$exists": True}, "y": {"$exists": True}}))
all_data = list(listeria_collection.find({
    "x": {"$exists": True},
    "y": {"$exists": True},
    "fresh_smoked": "Fresh"
}))

if not all_data:
    st.warning("No data found with X and Y coordinates in MongoDB.")
else:
    df = pd.DataFrame(all_data)
    df['sample_date'] = pd.to_datetime(df['sample_date']).dt.date

    available_dates = df['sample_date'].dropna().unique()
    selected_date = st.selectbox("Select Date", sorted(available_dates, reverse=True))

    if selected_date:
        filtered = df[df['sample_date'] == selected_date].copy()
        filtered = filtered.rename(columns={"point": "points"})

        if not filtered.empty:
            filtered['points'] = filtered['points'].astype(str)
            filtered['x'] = pd.to_numeric(filtered['x'], errors='coerce')
            filtered['y'] = pd.to_numeric(filtered['y'], errors='coerce')
            filtered['value'] = pd.to_numeric(filtered['value'], errors='coerce')
            if 'description' not in filtered.columns:
                filtered['description'] = ""

            # --- Last 28 days history ---
            start_date_28 = selected_date - timedelta(days=27)
            recent_data = df[(df['sample_date'] >= start_date_28) & (df['sample_date'] <= selected_date)].copy()
            recent_data = recent_data.rename(columns={"point": "points"})
            recent_data['points'] = recent_data['points'].astype(str)
            recent_data['value'] = pd.to_numeric(recent_data['value'], errors='coerce')

            recent_lookup = recent_data.groupby('points').apply(
                lambda x: "<br>&nbsp;&nbsp;".join(
                    x.sort_values('sample_date', ascending=False).apply(
                        lambda row: f"{row['sample_date']}: {'<b style=\"color:red\">Detected</b>' if row['value'] == 1 else '<b style=\"color:green\">Not Detected</b>' if row['value'] == 0 else 'Unknown'}",
                        axis=1))
            )

            filtered['history'] = filtered['points'].map(recent_lookup).fillna("No history available")

            # --- Last 28 days positivity analysis ---
            start_date_28 = selected_date - timedelta(days=27)
            window_data = df[(df['sample_date'] >= start_date_28) & (df['sample_date'] <= selected_date)].copy()
            window_data = window_data.rename(columns={"point": "points"})
            window_data['points'] = window_data['points'].astype(str)
            window_data['value'] = pd.to_numeric(window_data['value'], errors='coerce')

            def determine_color(pos_ratio):
                if pos_ratio >= 0.5:
                    return "#8B0000"  # blood red
                elif pos_ratio > 0.2:
                    return "#FF0000"  # red
                elif pos_ratio > 0.0:
                    return "#FFBF00"  # amber
                else:
                    return "#008000"  # green

            positivity_ratio = (
                window_data.groupby("points")["value"]
                .agg(lambda vals: np.mean(vals.dropna()) if not vals.dropna().empty else np.nan)
            )

            positivity_colors = positivity_ratio.map(determine_color)
            positivity_percents = (positivity_ratio * 100).round(1).astype(str) + '%'
            filtered["dot_color"] = filtered["points"].map(positivity_colors).fillna("#A9A9A9")  # gray default
            filtered["positivity"] = filtered["points"].map(positivity_percents).fillna("N/A")

          
            filtered['hover_text'] = (
                "<b>Location Code:</b> " + filtered['location_code'].astype(str) + "<br>"
                + "<b>28-Day Positivity:</b> " + filtered['positivity'] + "<br>"
                + "<b>Last 28 Days:</b><br>&nbsp;&nbsp;" + filtered['history']
            )

            # --- Plot ---
            fig = go.Figure()
            fig.add_layout_image(
                dict(
                    source=image_base64,
                    xref="x",
                    yref="y",
                    x=0,
                    y=height,
                    sizex=width,
                    sizey=height,
                    sizing="contain",
                    layer="below"
                )
            )

            fig.add_trace(go.Scatter(
                x=filtered['x'],
                y=height - filtered['y'],
                mode='markers',
                marker=dict(
                    size=12,
                    color=filtered['dot_color'],
                    line=dict(width=1, color='DarkSlateGrey')
                ),
                customdata=filtered[['hover_text']],
                hovertemplate="%{customdata[0]}<extra></extra>"
            ))

            fig.update_layout(
                xaxis=dict(visible=False, range=[0, width]),
                yaxis=dict(visible=False, range=[0, height]),
                showlegend=False,
                margin=dict(l=0, r=0, t=40, b=0),
                title=f"Fresh Department Detections on {selected_date}"
            )

            st.plotly_chart(fig, use_container_width=True)
                                 
          
        else:
            st.warning("No data found for the selected date.")


#################################
# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# import cv2
# import numpy as np
# import os
# from pymongo import MongoClient
# from datetime import datetime, timedelta
# import plotly.graph_objects as go
# from PIL import Image
# import base64
# from io import BytesIO

# # MongoDB connection
# client = MongoClient(st.secrets["MONGO_URI"])
# db = client["koral"]
# listeria_collection = db["listeria"]

# def load_image_base64(image_path="koral6_3.png"):
#     if not os.path.exists(image_path):
#         st.error(f"Image not found at {image_path}")
#         return None, None, (0, 0)
#     image = Image.open(image_path)
#     buffered = BytesIO()
#     image.save(buffered, format="PNG")
#     img_str = base64.b64encode(buffered.getvalue()).decode()
#     return image, f"data:image/png;base64,{img_str}", image.size  # (width, height)

# # ---- Streamlit App ----
# st.set_page_config(page_title="Fresh Map", page_icon="🧫", layout="wide")

# # Load image for background
# image_pil, image_base64, (width, height) = load_image_base64()

# # Get data with x and y
# all_data = list(listeria_collection.find({
#     "x": {"$exists": True},
#     "y": {"$exists": True},
#     "fresh_smoked": "Fresh"
# }))

# if not all_data:
#     st.warning("No data found with X and Y coordinates in MongoDB.")
# else:
#     df = pd.DataFrame(all_data)
#     df['sample_date'] = pd.to_datetime(df['sample_date']).dt.date

#     available_dates = df['sample_date'].dropna().unique()
#     selected_date = st.selectbox("Select Date", sorted(available_dates, reverse=True))

#     if selected_date:
#         filtered = df[df['sample_date'] == selected_date].copy()
#         filtered = filtered.rename(columns={"point": "points"})

#         if not filtered.empty:
#             filtered['points'] = filtered['points'].astype(str)
#             filtered['x'] = pd.to_numeric(filtered['x'], errors='coerce')
#             filtered['y'] = pd.to_numeric(filtered['y'], errors='coerce')
#             filtered['value'] = pd.to_numeric(filtered['value'], errors='coerce')
#             if 'description' not in filtered.columns:
#                 filtered['description'] = ""

#             # --- Last 28 days history ---
#             start_date_28 = selected_date - timedelta(days=27)
#             recent_data = df[(df['sample_date'] >= start_date_28) & (df['sample_date'] <= selected_date)].copy()
#             recent_data = recent_data.rename(columns={"point": "points"})
#             recent_data['points'] = recent_data['points'].astype(str)
#             recent_data['value'] = pd.to_numeric(recent_data['value'], errors='coerce')

#             recent_lookup = recent_data.groupby('points').apply(
#                 lambda x: "<br>&nbsp;&nbsp;".join(
#                     x.sort_values('sample_date', ascending=False).apply(
#                         lambda row: f"{row['sample_date']}: {'<b style=\"color:red\">Detected</b>' if row['value'] == 1 else '<b style=\"color:green\">Not Detected</b>' if row['value'] == 0 else 'Unknown'}",
#                         axis=1))
#             )

#             filtered['history'] = filtered['points'].map(recent_lookup).fillna("No history available")

#             # --- 28-day positivity ---
#             window_data = df[(df['sample_date'] >= start_date_28) & (df['sample_date'] <= selected_date)].copy()
#             window_data = window_data.rename(columns={"point": "points"})
#             window_data['points'] = window_data['points'].astype(str)
#             window_data['value'] = pd.to_numeric(window_data['value'], errors='coerce')

#             def determine_color(pos_ratio):
#                 if pos_ratio >= 0.5:
#                     return "#8B0000"  # blood red
#                 elif pos_ratio > 0.2:
#                     return "#FF0000"  # red
#                 elif pos_ratio > 0.0:
#                     return "#FFBF00"  # amber
#                 else:
#                     return "#008000"  # green

#             positivity_ratio = (
#                 window_data.groupby("points")["value"]
#                 .agg(lambda vals: np.mean(vals.dropna()) if not vals.dropna().empty else np.nan)
#             )

#             positivity_colors = positivity_ratio.map(determine_color)
#             positivity_percents = (positivity_ratio * 100).round(1).astype(str) + '%'
#             filtered["dot_color"] = filtered["points"].map(positivity_colors).fillna("#A9A9A9")
#             filtered["positivity"] = filtered["points"].map(positivity_percents).fillna("N/A")

#             filtered['hover_text'] = (
#                 "<b>Location Code:</b> " + filtered['location_code'].astype(str) + "<br>"
#                 + "<b>28-Day Positivity:</b> " + filtered['positivity'] + "<br>"
#                 + "<b>Last 28 Days:</b><br>&nbsp;&nbsp;" + filtered['history']
#             )

#             # Split into Before and During Production
#             before_df = filtered[filtered['before_during'] == 'BP'].copy()
#             during_df = filtered[filtered['before_during'] == 'DP'].copy()

#             col1, col2 = st.columns(2)

#             def plot_map(sub_df, title):
#                 fig = go.Figure()
#                 fig.add_layout_image(
#                     dict(
#                         source=image_base64,
#                         xref="x", yref="y",
#                         x=0, y=height,
#                         sizex=width, sizey=height,
#                         sizing="contain",
#                         layer="below"
#                     )
#                 )

#                 fig.add_trace(go.Scatter(
#                     x=sub_df['x'],
#                     y=height - sub_df['y'],  # Correct Y inversion for image coordinates
#                     mode='markers',
#                     marker=dict(
#                         size=12,
#                         color=sub_df['dot_color'],
#                         line=dict(width=1, color='DarkSlateGrey')
#                     ),
#                     customdata=sub_df[['hover_text']],
#                     hovertemplate="%{customdata[0]}<extra></extra>"
#                 ))

#                 fig.update_layout(
#                     xaxis=dict(visible=False, range=[0, width]),
#                     yaxis=dict(visible=False, range=[0, height]),
#                     showlegend=False,
#                     margin=dict(l=0, r=0, t=40, b=0),
#                     title=title
#                 )
#                 return fig

#             with col1:
#                 st.plotly_chart(plot_map(before_df, "Before Production"), use_container_width=True)

#             with col2:
#                 st.plotly_chart(plot_map(during_df, "During Production"), use_container_width=True)

#         else:
#             st.warning("No data found for the selected date.")


###################################


# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# import cv2
# import numpy as np
# import os
# from pymongo import MongoClient
# from datetime import datetime, timedelta
# import plotly.graph_objects as go
# from PIL import Image
# import base64
# from io import BytesIO

# # MongoDB connection
# client = MongoClient(st.secrets["MONGO_URI"])
# db = client["koral"]
# listeria_collection = db["listeria"]

# def load_image_base64(image_path="koral6_3.png"):
#     if not os.path.exists(image_path):
#         st.error(f"Image not found at {image_path}")
#         return None, None, (0, 0)
#     image = Image.open(image_path)
#     buffered = BytesIO()
#     image.save(buffered, format="PNG")
#     img_str = base64.b64encode(buffered.getvalue()).decode()
#     return image, f"data:image/png;base64,{img_str}", image.size  # (width, height)

# # ---- Streamlit App ----
# st.set_page_config(page_title="Fresh Map", page_icon="🧫", layout="wide")

# # Load image for background
# image_pil, image_base64, (width, height) = load_image_base64()

# # Get data with x and y
# all_data = list(listeria_collection.find({
#     "x": {"$exists": True},
#     "y": {"$exists": True},
#     "fresh_smoked": "Fresh"
# }))

# if not all_data:
#     st.warning("No data found with X and Y coordinates in MongoDB.")
# else:
#     df = pd.DataFrame(all_data)
#     df['sample_date'] = pd.to_datetime(df['sample_date']).dt.date

#     available_dates = df['sample_date'].dropna().unique()
#     selected_date = st.selectbox("Select Date", sorted(available_dates, reverse=True))

#     if selected_date:
#         filtered = df[df['sample_date'] == selected_date].copy()
#         filtered = filtered.rename(columns={"point": "points"})

#         if not filtered.empty:
#             filtered['points'] = filtered['points'].astype(str)
#             filtered['x'] = pd.to_numeric(filtered['x'], errors='coerce')
#             filtered['y'] = pd.to_numeric(filtered['y'], errors='coerce')
#             filtered['value'] = pd.to_numeric(filtered['value'], errors='coerce')
#             if 'description' not in filtered.columns:
#                 filtered['description'] = ""

#             # --- Last 28 days history ---
#             start_date_28 = selected_date - timedelta(days=27)
#             recent_data = df[(df['sample_date'] >= start_date_28) & (df['sample_date'] <= selected_date)].copy()
#             recent_data = recent_data.rename(columns={"point": "points"})
#             recent_data['points'] = recent_data['points'].astype(str)
#             recent_data['value'] = pd.to_numeric(recent_data['value'], errors='coerce')

#             recent_lookup = recent_data.groupby('points').apply(
#                 lambda x: "<br>&nbsp;&nbsp;".join(
#                     x.sort_values('sample_date', ascending=False).apply(
#                         lambda row: f"{row['sample_date']}: {'<b style=\"color:red\">Detected</b>' if row['value'] == 1 else '<b style=\"color:green\">Not Detected</b>' if row['value'] == 0 else 'Unknown'}",
#                         axis=1))
#             )

#             filtered['history'] = filtered['points'].map(recent_lookup).fillna("No history available")

#             # --- 28-day positivity ---
#             window_data = df[(df['sample_date'] >= start_date_28) & (df['sample_date'] <= selected_date)].copy()
#             window_data = window_data.rename(columns={"point": "points"})
#             window_data['points'] = window_data['points'].astype(str)
#             window_data['value'] = pd.to_numeric(window_data['value'], errors='coerce')

#             def determine_color(pos_ratio):
#                 if pos_ratio >= 0.5:
#                     return "#8B0000"  # blood red
#                 elif pos_ratio > 0.2:
#                     return "#FF0000"  # red
#                 elif pos_ratio > 0.0:
#                     return "#FFBF00"  # amber
#                 else:
#                     return "#008000"  # green

#             positivity_ratio = (
#                 window_data.groupby("points")["value"]
#                 .agg(lambda vals: np.mean(vals.dropna()) if not vals.dropna().empty else np.nan)
#             )

#             positivity_colors = positivity_ratio.map(determine_color)
#             positivity_percents = (positivity_ratio * 100).round(1).astype(str) + '%'
#             filtered["dot_color"] = filtered["points"].map(positivity_colors).fillna("#A9A9A9")
#             filtered["positivity"] = filtered["points"].map(positivity_percents).fillna("N/A")

#             filtered['hover_text'] = (
#                 "<b>Location Code:</b> " + filtered['location_code'].astype(str) + "<br>"
#                 + "<b>28-Day Positivity:</b> " + filtered['positivity'] + "<br>"
#                 + "<b>Last 28 Days:</b><br>&nbsp;&nbsp;" + filtered['history']
#             )

#             # Split into Before and During Production
#             before_df = filtered[filtered['before_during'] == 'BP']
#             during_df = filtered[filtered['before_during'] == 'DP']

#             col1, col2 = st.columns(2)

#             def plot_map(sub_df, title):
#                 fig = go.Figure()
#                 fig.add_layout_image(
#                     dict(
#                         source=image_base64,
#                         xref="x", yref="y",
#                         x=0, y=height,
#                         sizex=width, sizey=height,
#                         sizing="contain",
#                         layer="below"
#                     )
#                 )

#                 fig.add_trace(go.Scatter(
#                     x=sub_df['x'],
#                     y=height - sub_df['y'],
#                     mode='markers',
#                     marker=dict(
#                         size=12,
#                         color=sub_df['dot_color'],
#                         line=dict(width=1, color='DarkSlateGrey')
#                     ),
#                     customdata=sub_df[['hover_text']],
#                     hovertemplate="%{customdata[0]}<extra></extra>"
#                 ))

#                 fig.update_layout(
#                     xaxis=dict(visible=False, range=[0, width]),
#                     yaxis=dict(visible=False, range=[0, height]),
#                     showlegend=False,
#                     margin=dict(l=0, r=0, t=40, b=0),
#                     title=title
#                 )
#                 return fig

#             with col1:
#                 st.plotly_chart(plot_map(before_df, "Before Production"), use_container_width=True)

#             with col2:
#                 st.plotly_chart(plot_map(during_df, "During Production"), use_container_width=True)

#         else:
#             st.warning("No data found for the selected date.")

