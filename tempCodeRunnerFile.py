import streamlit as st
import json
import random
import datetime
import os
import re
import qrcode
from io import BytesIO
import smtplib
from email.message import EmailMessage

# ---------------------- FILE PATHS ----------------------
BOOKINGS_FILE = "Railway_data.json"
USERS_FILE = "users.json"

# ---------------------- LOAD & SAVE ----------------------
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# ---------------------- SESSION INIT ----------------------
if 'bookings' not in st.session_state:
    st.session_state.bookings = load_json(BOOKINGS_FILE)
if 'users' not in st.session_state:
    st.session_state.users = load_json(USERS_FILE)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'otp_store' not in st.session_state:
    st.session_state.otp_store = {}
if 'trains' not in st.session_state:
    st.session_state.trains = [
        {"train_no": "T101", "name": "Express A", "from": "Delhi", "to": "Mumbai", "departure": "09:00", "arrival": "18:00", "seats": {"SL": 10, "3A": 8, "2A": 5}},
        {"train_no": "UP104", "name": "Lucknow Mail", "from": "Delhi", "to": "Lucknow", "departure": "22:00", "arrival": "06:00", "seats": {"SL": 25, "3A": 15, "2A": 8}},
        {"train_no": "UP105", "name": "Kanpur Intercity", "from": "Kanpur", "to": "Delhi", "departure": "05:00", "arrival": "11:00", "seats": {"SL": 20, "3A": 10, "2A": 5}},
    ]

fare_chart = {"SL": 600, "3A": 1000, "2A": 1500}

# ---------------------- UTILITIES ----------------------
def generate_pnr():
    return str(random.randint(1000000000000, 9999999999999))

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def send_otp_email(to_email):
    otp = str(random.randint(100000, 999999))
    st.session_state.otp_store[to_email] = otp
    msg = EmailMessage()
    msg['Subject'] = 'Your OTP for Railway Booking'
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = to_email
    msg.set_content(f'Your OTP is: {otp}')
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('Ayushbro779@gmail.com', 'okaupcpqfgudzygc')
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send OTP: {e}")
        return False

def verify_otp(email, entered_otp):
    return st.session_state.otp_store.get(email) == entered_otp

def valid_journey_date(journey_date):
    today = datetime.date.today()
    return 0 <= (journey_date - today).days <= 60

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# ---------------------- AUTH PAGES ----------------------
def register_page():
    st.title("🆕 Register New Account")
    email = st.text_input("Email Address", key="register_email").strip().lower()
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("📧 Send OTP"):
        if not validate_email(email):
            st.error("Invalid email format!")
        elif email in st.session_state.users:
            st.error("Account already exists. Please login.")
        elif password != confirm:
            st.error("Passwords do not match!")
        else:
            if send_otp_email(email):
                st.success("OTP sent! Check your email.")
                st.session_state.pending_register = {"email": email, "password": password}

    if 'pending_register' in st.session_state:
        otp_input = st.text_input("Enter OTP sent to your email")
        if st.button("✅ Verify OTP"):
            if verify_otp(st.session_state.pending_register['email'], otp_input):
                email = st.session_state.pending_register['email']
                st.session_state.users[email] = {"password": st.session_state.pending_register['password'], "bookings": []}
                save_json(USERS_FILE, st.session_state.users)
                st.success("Registration successful! Please login now.")
                del st.session_state.pending_register
            else:
                st.error("Invalid OTP!")

def login_page():
    st.title("🔐 Login to Your Account")
    email = st.text_input("Email Address", key="login_email").strip().lower()

    if st.button("📨 Send OTP"):
        if email not in st.session_state.users:
            st.error("No account found. Please register first.")
        else:
            if send_otp_email(email):
                st.success("OTP sent to your email!")
                st.session_state.pending_login = email

    if 'pending_login' in st.session_state:
        otp_input = st.text_input("Enter OTP sent to your email")
        if st.button("🔓 Verify Login"):
            if verify_otp(st.session_state.pending_login, otp_input):
                st.session_state.logged_in = True
                st.session_state.current_user = st.session_state.pending_login
                st.success(f"Welcome back, {st.session_state.current_user}!")
                del st.session_state.pending_login
                st.rerun()
            else:
                st.error("Invalid OTP!")

# ---------------------- MAIN UI ----------------------
def main():
    st.set_page_config(page_title="🚄 Indian Railway Booking", page_icon="🚉", layout="wide")
    
    # ✨ Animated Header
    st.markdown("""
        <div style="text-align:center; margin-top:10px; margin-bottom:20px;">
            <h1>🚄 Indian Railway Booking System</h1>
            <p style="color:#444; font-size:18px;">
                🌟 <b>Book</b>, <b>Track</b> & <b>Manage</b> your tickets with comfort and ease.<br>
                <i>Powered by Streamlit & Python 💻</i>
            </p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["🔐 Login", "🆕 Register"])
        with tab1: login_page()
        with tab2: register_page()
    else:
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/7435/7435267.png", width=100)
            st.success("Logged in as:")
            st.info(st.session_state.current_user)
            st.divider()
            menu = st.radio("Navigation", ["🚆 Book Ticket", "📜 My Bookings", "✏️ Edit Booking", "🔍 Track PNR", "🗑️ Clear Bookings"], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.rerun()

        # Placeholder for your functional pages
        if menu == "🚆 Book Ticket":
            st.write("Booking page content here...")
        elif menu == "📜 My Bookings":
            st.write("My bookings content here...")
        elif menu == "✏️ Edit Booking":
            st.write("Edit booking content here...")
        elif menu == "🔍 Track PNR":
            st.write("Track PNR content here...")
        elif menu == "🗑️ Clear Bookings":
            st.write("Clear bookings content here...")

# ---------------------- STYLING ----------------------
def custom_style():
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] {
                background: linear-gradient(120deg, #f8fbff 0%, #e9f3ff 100%);
                font-family: 'Poppins', sans-serif;
                color: #1a1a1a;
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(160deg, #004aad 0%, #0078ff 100%) !important;
                color: white !important;
            }
            div.stButton > button {
                background: linear-gradient(135deg, #0078ff, #00a8ff);
                color: white;
                border-radius: 10px;
                font-weight: 600;
                padding: 10px 22px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
            }
            div.stButton > button:hover {
                background: linear-gradient(135deg, #00a8ff, #0078ff);
                transform: scale(1.05);
            }
            hr {
                border: 1px solid #0078ff20;
                margin: 1.5em 0;
            }
        </style>
    """, unsafe_allow_html=True)

# ---------------------- RUN APP ----------------------
if __name__ == "__main__":
    custom_style()
    main()
