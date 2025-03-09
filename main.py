import streamlit as st
import google.generativeai as genai
import pdfkit
import os
from io import BytesIO
import bcrypt
import json

# Configure Gemini API
genai.configure(api_key="AIzaSyBCNZBnzqNUkmfKLRbOrA9wOw1VaOzQ86Q")

# User Authentication (Basic File-Based)
USER_CREDENTIALS_FILE = "users.json"

def load_users():
    if os.path.exists(USER_CREDENTIALS_FILE):
        with open(USER_CREDENTIALS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open(USER_CREDENTIALS_FILE, "w") as file:
        json.dump(users, file)

def register_user(username, email, password, confirm_password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    if password != confirm_password:
        return False, "Passwords do not match."
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = {"email": email, "password": hashed_pw}
    save_users(users)
    return True, "Registration successful. Please log in."

def authenticate_user(username, password):
    users = load_users()
    if username in users and bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
        return True
    return False

def generate_study_plan(subjects, hours_per_day, preferences):
    prompt = f"""
    Create a study plan for the following subjects: {', '.join(subjects)}.
    The student has {hours_per_day} hours per day to study and prefers {preferences}.
    Provide a structured, balanced schedule.
    """
    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text if response else "Error generating study plan."

# Initialize Session State for Authentication
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "show_login_after_registration" not in st.session_state:
    st.session_state.show_login_after_registration = False
if "reg_username" not in st.session_state:
    st.session_state.reg_username = ""

# Profile Section (Top Right)
if st.session_state.user_authenticated:
    with st.sidebar.expander(f"👤 {st.session_state.logged_in_user}"):
        st.write("My Profile")
        if st.button("Logout", key=f"logout_button_{st.session_state.logged_in_user}"):
            st.session_state.user_authenticated = False
            st.session_state.logged_in_user = None
            st.rerun()

st.title("Studbud: AI Personalized Study Planner")

# Sidebar Navigation
menu = st.sidebar.selectbox("Navigation", ["Login", "Register"] if not st.session_state.user_authenticated else ["Dashboard", "Logout"])

if menu == "Register":
    st.sidebar.header("Create an Account")

    # Ensure session state key is initialized before using it in the text input
    if "reg_username" not in st.session_state:
        st.session_state.reg_username = ""

    reg_username = st.sidebar.text_input("Username", key="reg_username")
    reg_email = st.sidebar.text_input("Email", key="reg_email")
    reg_password = st.sidebar.text_input("Password", type="password", key="reg_password")
    reg_confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="reg_confirm_password")

    if st.sidebar.button("Register"):
        if reg_username and reg_email and reg_password and reg_confirm_password:
            success, message = register_user(reg_username, reg_email, reg_password, reg_confirm_password)
            if success:
                st.sidebar.success(message)
                st.session_state.show_login_after_registration = True
                st.session_state["reg_username"] = reg_username  # ✅ Set session state using dictionary notation
                st.rerun()
            else:
                st.sidebar.error(message)
        else:
            st.sidebar.error("All fields are required.")
elif menu == "Login" or st.session_state.show_login_after_registration:
    st.sidebar.header("User Login")
    default_username = st.session_state.get("reg_username", "")
    login_username = st.sidebar.text_input("Username", value=default_username)
    login_password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if login_username.strip() and login_password.strip():
            if authenticate_user(login_username, login_password):
                st.sidebar.success("Login successful!")
                st.session_state.user_authenticated = True
                st.session_state.logged_in_user = login_username
                st.session_state.show_login_after_registration = False
                st.session_state.reg_username = ""
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password.")
        else:
            st.sidebar.error("Please enter both username and password.")

elif menu == "Logout":
    st.session_state.user_authenticated = False
    st.session_state.logged_in_user = None
    st.rerun()

if st.session_state.user_authenticated:
    st.sidebar.header("Input Your Preferences")
    subjects = st.sidebar.multiselect("Select Subjects", ["Math", "Science", "History", "English", "Programming"])
    hours_per_day = st.sidebar.slider("Study Hours per Day", 1, 10, 3)
    preferences = st.sidebar.text_input("Preferred Study Methods", "Flashcards, Practice Tests")

    if st.sidebar.button("Generate Study Plan"):
        if subjects:
            study_plan = generate_study_plan(subjects, hours_per_day, preferences)
            st.subheader("Your Personalized Study Plan")
            st.write(study_plan)

            def generate_pdf(plan):
                pdf = pdfkit.from_string(plan, False)
                return BytesIO(pdf)

            pdf_button = st.button("Download Study Plan as PDF")
            if pdf_button:
                pdf_data = generate_pdf(study_plan)
                st.download_button(label="Download PDF", data=pdf_data, file_name="study_plan.pdf", mime="application/pdf")
        else:
            st.warning("Please select at least one subject.")
else:
    st.warning("Please login to generate your study plan.")

st.sidebar.markdown("---")
st.sidebar.markdown("Developed with ❤️ using Streamlit and Gemini AI.")
