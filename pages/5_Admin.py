import streamlit as st
import pandas as pd
from utils.db import listeria_collection

# 🔐 Check if user is logged in
if "user" not in st.session_state:
    st.warning("Please log in to access this page.")
    st.stop()

# 🛡️ Restrict to admins only
if st.session_state.get("user", {}).get("role") != "admin":
    st.error("You do not have permission to access this page.")
    st.stop()

# 👤 Display user info and logout option
st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.user['username']}`")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.success("🔓 Logged out successfully.")
    st.stop()

# 📁 Upload section
st.title("📁 Admin: Upload Listeria Results Data")

uploaded_file = st.file_uploader("Upload Results File", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8", encoding_errors="replace")
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.stop()

    st.write(df.head())  # Preview data

    # ✅ Required columns
    required_columns = {
        "sample_code", "sample_description", "translated_description", "test_code", "test_result", "unit",
        "analytical_report_code", "sample_date", "location_code", "fresh_smoked", "sub_area",
        "before_during", "value", "week_num", "week", "x", "y", "points"
    }

    if not required_columns.issubset(df.columns):
        st.error(f"Missing required columns: {', '.join(required_columns - set(df.columns))}")
        st.stop()

    # 🕓 Date parsing
    df["sample_date"] = pd.to_datetime(df["sample_date"], format="%d-%m-%Y", errors="coerce")
    df["sample_date"] = df["sample_date"].where(df["sample_date"].notna(), None)

    # 🧑 Add uploader info
    username = st.session_state.user.get("username", "admin")
    df["uploaded_by"] = username

    # 📤 Upload to MongoDB
    if st.button("Upload to MongoDB"):
        try:
            data_list = df.to_dict(orient="records")
            result = listeria_collection.insert_many(data_list)
            st.success(f"✅ Inserted {len(result.inserted_ids)} records into the database!")
        except Exception as e:
            st.error(f"❌ Database Error: {e}")

# 📥 Download existing MongoDB collection as CSV
st.subheader("📥 Download MongoDB Data")

try:
    data = list(listeria_collection.find({}))
    if not data:
        st.warning("⚠️ No data found in the collection.")
    else:
        df_export = pd.DataFrame(data)
        if "_id" in df_export.columns:
            df_export.drop(columns=["_id"], inplace=True)
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Download Listeria Collection as CSV",
            data=csv,
            file_name="listeria_data.csv",
            mime="text/csv"
        )
except Exception as e:
    st.error(f"❌ Failed to export data: {e}")

# 🛠️ Admin Tool to Correct X, Y Coordinates
st.subheader("🛠️ Update X/Y Coordinates for a Location Code")

try:
    location_codes = listeria_collection.distinct("location_code")
    if location_codes:
        selected_code = st.selectbox("Select Location Code", sorted([str(code) for code in location_codes if code]))

        with st.form("xy_update_form"):
            new_x = st.number_input("New X Coordinate", min_value=0.0, step=1.0)
            new_y = st.number_input("New Y Coordinate", min_value=0.0, step=1.0)
            update_btn = st.form_submit_button("Update Coordinates")

            if update_btn:
                result = listeria_collection.update_many(
                    {"location_code": selected_code},
                    {"$set": {"x": new_x, "y": new_y}}
                )
                st.success(f"✅ Updated {result.modified_count} record(s) for location_code = '{selected_code}'.")
    else:
        st.info("No location_code values found in database.")
except Exception as e:
    st.error(f"Error loading location codes: {e}")

