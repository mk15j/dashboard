import streamlit as st
from utils.auth import authenticate  # Make sure this path is correct
# from streamlit.source_util import get_pages

# pages = get_pages("app.py")  # Replace with your actual main file name if different
# st.write("Available pages:", list(pages.keys()))
# for key, page in pages.items():
# st.write(f"{page['page_name']}")
st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
# st.write(f"{page['page_name']}")
if st.button("Login"):
    user = authenticate(username, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome, {user['username']}!")
        st.switch_page("pages/2_Trend_Analysis.py")  # ✅ Correct title, not filename
    else:
        st.error("Invalid username or password")

