# 🚆 Indian Railway Booking System | Python + Streamlit + OTP + QR Ticket

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

A complete **Indian Railway Booking System** built using **Python** and **Streamlit**, featuring **OTP-based login**, **QR ticket generation**, **PNR tracking**, and **JSON-based data management**.  
This project simulates a real-world train ticket booking platform with modern UI and real-time data handling.

---

## 🧭 **Project Overview**

This Railway Booking System lets users:
- 🔐 Login/Register securely using **Email OTP**
- 🚆 View and select trains
- 💺 Book tickets with class and fare options
- 🧾 Get a **QR-coded e-ticket**
- 🔎 Track tickets using **PNR number**
- ✏️ Edit or cancel bookings anytime
- 💾 Store data persistently in **JSON**

It’s a beginner-friendly yet professional project demonstrating **Streamlit**, **JSON handling**, **Email automation**, and **QR code generation** — perfect for students or Python developers.

---

## 🎯 **Objectives**

- Build a web-based booking system using **Streamlit**
- Implement **secure OTP authentication**
- Create **interactive forms** for booking and editing tickets
- Generate **QR-coded e-tickets**
- Store and manage booking data with **JSON**
- Track & manage PNR numbers dynamically

---

## 🧩 **Key Features**

| Feature | Description |
|----------|-------------|
| 🔐 OTP Login | Email-based OTP login for secure access |
| 👤 User Registration | Account creation with OTP verification |
| 🚆 Train List | View trains, routes, timings, and seat classes |
| 🎫 Booking System | Select train, class, date, and generate ticket |
| 💳 Fare Management | Dynamic fare calculation based on class |
| 📱 QR Ticket | Generates QR code containing ticket info |
| 🔍 Track PNR | Fetch ticket details by entering PNR number |
| ✏️ Edit/Cancel | Modify or cancel bookings anytime |
| 💾 Persistent Storage | Data saved in JSON for reusability |
| 🧭 Streamlit Navigation | Sidebar menu for seamless user flow |

---

## 🧱 **Tech Stack**

- **Frontend/UI:** Streamlit  
- **Backend:** Python  
- **Database:** JSON File Storage  
- **Authentication:** OTP via SMTP (Email)  
- **QR Generation:** `qrcode` library  
- **Email Handling:** `smtplib`, `email.message`

---

## 📂 **Project Structure**
│
├── app.py # Main Streamlit App
├── Railway_data.json # Stores booking details
├── users.json # Stores user credentials
├── requirements.txt # Required dependencies
└── README.md # Project Documentation

📊 Flow Diagram
[ Login/Register ] 
        ↓
[ OTP Verification ]
        ↓
[ Train Selection ]
        ↓
[ Book Ticket ]
        ↓
[ Generate PNR + QR ]
        ↓
[ View/Edit/Cancel Ticket ]


📧 OTP Email Configuration

To enable OTP login via Gmail:

Go to Google App Passwords

Generate a new password for “Mail”

Replace these lines in your code:

EMAIL_ADDRESS = "youremail@gmail.com"
EMAIL_PASSWORD = "your-app-password"
