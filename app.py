import base64
import datetime
import json
import os
import random
import re
import smtplib
from email.message import EmailMessage
from functools import wraps
from io import BytesIO

import qrcode
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BOOKINGS_FILE = "Railway_data.json"
USERS_FILE = "users.json"


TRAINS = [
    {
        "train_no": "T101",
        "name": "Express A",
        "from": "Delhi",
        "to": "Mumbai",
        "departure": "09:00",
        "arrival": "18:00",
        "seats": {"SL": 10, "3A": 8, "2A": 5},
    },
    {
        "train_no": "T202",
        "name": "Rajdhani B",
        "from": "Delhi",
        "to": "Kolkata",
        "departure": "10:00",
        "arrival": "20:00",
        "seats": {"SL": 12, "3A": 6, "2A": 4},
    },
    {
        "train_no": "T303",
        "name": "Duronto C",
        "from": "Delhi",
        "to": "Chennai",
        "departure": "07:00",
        "arrival": "22:00",
        "seats": {"SL": 15, "3A": 10, "2A": 6},
    },
    {
        "train_no": "UP101",
        "name": "Gomti Express",
        "from": "Lucknow",
        "to": "Delhi",
        "departure": "06:00",
        "arrival": "13:30",
        "seats": {"SL": 15, "3A": 10, "2A": 6},
    },
    {
        "train_no": "UP102",
        "name": "Prayagraj Express",
        "from": "Prayagraj",
        "to": "Delhi",
        "departure": "21:30",
        "arrival": "07:00",
        "seats": {"SL": 20, "3A": 12, "2A": 8},
    },
    {
        "train_no": "UP103",
        "name": "Varanasi Shatabdi",
        "from": "Varanasi",
        "to": "Delhi",
        "departure": "06:30",
        "arrival": "15:00",
        "seats": {"SL": 18, "3A": 12, "2A": 6},
    },
    {
        "train_no": "UP104",
        "name": "Lucknow Mail",
        "from": "Delhi",
        "to": "Lucknow",
        "departure": "22:00",
        "arrival": "06:00",
        "seats": {"SL": 25, "3A": 15, "2A": 8},
    },
    {
        "train_no": "UP105",
        "name": "Kanpur Intercity",
        "from": "Kanpur",
        "to": "Delhi",
        "departure": "05:00",
        "arrival": "11:00",
        "seats": {"SL": 20, "3A": 10, "2A": 5},
    },
    {
        "train_no": "UP106",
        "name": "Gorakhpur Express",
        "from": "Gorakhpur",
        "to": "Lucknow",
        "departure": "08:00",
        "arrival": "14:00",
        "seats": {"SL": 18, "3A": 12, "2A": 6},
    },
    {
        "train_no": "UP107",
        "name": "Agra Intercity",
        "from": "Agra",
        "to": "Lucknow",
        "departure": "07:00",
        "arrival": "13:00",
        "seats": {"SL": 14, "3A": 10, "2A": 6},
    },
    {
        "train_no": "UP108",
        "name": "Meerut Express",
        "from": "Delhi",
        "to": "Meerut",
        "departure": "08:30",
        "arrival": "10:30",
        "seats": {"SL": 30, "3A": 12, "2A": 5},
    },
    {
        "train_no": "UP109",
        "name": "Bareilly Mail",
        "from": "Bareilly",
        "to": "Delhi",
        "departure": "05:45",
        "arrival": "12:00",
        "seats": {"SL": 18, "3A": 8, "2A": 4},
    },
    {
        "train_no": "UP110",
        "name": "Noida Express",
        "from": "Lucknow",
        "to": "Noida",
        "departure": "09:30",
        "arrival": "16:30",
        "seats": {"SL": 15, "3A": 10, "2A": 5},
    },
]


FARE_CHART = {"SL": 600, "3A": 1000, "2A": 1500}


app = Flask(__name__)
app.secret_key = "replace-this-with-a-secure-random-value"

EMAIL_USER = os.environ.get("RAILWAY_APP_EMAIL", "ayushbro779@gmail.com")
EMAIL_PASS = os.environ.get("RAILWAY_APP_EMAIL_PASSWORD", "okaupcpqfgudzygc")
OTP_EXPIRY_MINUTES = 5
OTP_STORE: dict[str, dict[str, datetime.datetime | str]] = {}
PENDING_REGISTRATION: dict[str, str] = {}


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def send_email(subject, body, to_email, attachments=None):
    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError("Email credentials are not configured.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg.set_content(body)

    attachments = attachments or []
    for attachment in attachments:
        filename, mime_type, data = attachment
        maintype, subtype = mime_type.split("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email):
    otp = generate_otp()
    OTP_STORE[email] = {
        "otp": otp,
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES),
    }
    body = (
        "Indian Railway Booking System\n\n"
        f"Your One Time Password (OTP) is: {otp}\n"
        f"This code is valid for {OTP_EXPIRY_MINUTES} minutes.\n\n"
        "If you did not request this, please ignore this email."
    )
    send_email("Your OTP for Railway Booking", body, email)


def verify_otp(email, otp):
    record = OTP_STORE.get(email)
    if not record:
        return False
    if record["expires_at"] < datetime.datetime.utcnow():
        del OTP_STORE[email]
        return False
    if record["otp"] != otp:
        return False
    del OTP_STORE[email]
    return True


def send_ticket_email(to_email, ticket, qr_bytes):
    journey_details = (
        f"PNR: {ticket['PNR']}\n"
        f"Train: {ticket['Train']} ({ticket['Train No']})\n"
        f"Route: {ticket['From']} → {ticket['To']}\n"
        f"Class: {ticket['Class']}\n"
        f"Journey Date: {ticket['Journey Date']}\n"
        f"Departure: {ticket['Departure']}\n"
        f"Arrival: {ticket['Arrival']}\n"
        f"Fare: ₹{ticket['Fare']}\n"
        f"Status: {ticket['Status']}\n"
    )
    body = (
        "Thank you for booking with Indian Railway Booking System.\n\n"
        "Your ticket details are below:\n\n"
        f"{journey_details}\n"
        "Scan the attached QR code at the station for quick access to your ticket.\n\n"
        "Have a safe journey!"
    )
    attachments = []
    if qr_bytes:
        attachments.append(("ticket_qr.png", "image/png", qr_bytes))
    send_email("Your Railway E-Ticket", body, to_email, attachments=attachments)


def get_users():
    return load_json(USERS_FILE)


def save_users(users):
    save_json(USERS_FILE, users)


def get_bookings():
    return load_json(BOOKINGS_FILE)


def save_bookings(bookings):
    save_json(BOOKINGS_FILE, bookings)


def generate_pnr():
    return str(random.randint(1000000000000, 9999999999999))


def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def qr_to_base64(data=None, buffer=None):
    if buffer is None:
        if data is None:
            raise ValueError("Either data or buffer must be provided for QR conversion.")
        buffer = generate_qr_code(data)
    else:
        buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def valid_journey_date(date_str):
    try:
        journey_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False

    today = datetime.date.today()
    delta = (journey_date - today).days
    return 0 <= delta <= 60


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_email" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def get_train(train_no):
    return next((train for train in TRAINS if train["train_no"] == train_no), None)


@app.context_processor
def inject_globals():
    return {
        "logged_in": "user_email" in session,
        "current_user": session.get("user_email"),
        "datetime": datetime,
    }


@app.template_filter("datetimeformat")
def datetimeformat(value, fmt="%Y-%m-%d"):
    if not value:
        return ""
    try:
        parsed = datetime.datetime.strptime(value, "%d-%m-%Y")
        return parsed.strftime(fmt)
    except ValueError:
        return value


@app.route("/")
def home():
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    bookings = get_bookings()
    user_bookings = [
        bookings[pnr]
        for pnr in get_users().get(session["user_email"], {}).get("bookings", [])
        if pnr in bookings
    ]
    return render_template("dashboard.html", trains=TRAINS, bookings=user_bookings)


@app.route("/register", methods=["GET", "POST"])
def register():
    form_data = {}
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        otp = request.form.get("otp", "").strip()
        form_data = {"email": email}

        users = get_users()
        errors = []

        if not email or not password:
            errors.append("Email and password are required.")
        elif not validate_email(email):
            errors.append("Invalid email address.")
        elif email in users:
            errors.append("Account already exists. Please log in.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        if "send_otp" in request.form:
            if errors:
                for error in errors:
                    flash(error, "danger")
            else:
                try:
                    send_otp_email(email)
                    PENDING_REGISTRATION[email] = password
                    flash("OTP sent to your email address.", "success")
                except RuntimeError as exc:
                    flash(str(exc), "danger")
                except Exception as exc:
                    app.logger.exception("Failed to send registration OTP", exc_info=exc)
                    flash("Unable to send OTP right now. Please try again later.", "danger")
        elif "register" in request.form:
            if errors:
                for error in errors:
                    flash(error, "danger")
            elif not otp:
                flash("Please enter the OTP sent to your email.", "danger")
            elif email not in PENDING_REGISTRATION:
                flash("Please request a new OTP before registering.", "warning")
            elif not verify_otp(email, otp):
                flash("Invalid or expired OTP. Please request a new one.", "danger")
            else:
                users[email] = {"password": password, "bookings": []}
                save_users(users)
                PENDING_REGISTRATION.pop(email, None)
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("login"))

    return render_template("register.html", form_data=form_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    form_data = {}
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        otp = request.form.get("otp", "").strip()
        form_data = {"email": email}

        users = get_users()

        if "send_otp" in request.form:
            if not email:
                flash("Please enter your registered email.", "danger")
            elif email not in users:
                flash("No account found for this email. Please register first.", "warning")
            else:
                try:
                    send_otp_email(email)
                    session["pending_login"] = email
                    flash("OTP sent to your email address.", "success")
                except RuntimeError as exc:
                    flash(str(exc), "danger")
                except Exception as exc:
                    app.logger.exception("Failed to send login OTP", exc_info=exc)
                    flash("Unable to send OTP right now. Please try again later.", "danger")
        elif "verify_otp" in request.form:
            if not email or email != session.get("pending_login"):
                flash("Please request an OTP for this email first.", "warning")
            elif not otp:
                flash("Please enter the OTP sent to your email.", "danger")
            elif not verify_otp(email, otp):
                flash("Invalid or expired OTP. Please request a new one.", "danger")
            else:
                session.pop("pending_login", None)
                session["user_email"] = email
                flash("Logged in successfully.", "success")
                return redirect(url_for("dashboard"))

    return render_template("login.html", form_data=form_data)


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    session.pop("pending_login", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/book", methods=["GET", "POST"])
@login_required
def book_ticket():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age")
        mobile = request.form.get("mobile", "").strip()
        nationality = request.form.get("nationality", "Indian").strip()
        address = request.form.get("address", "").strip()
        from_station = request.form.get("from_station", "").strip()
        to_station = request.form.get("to_station", "").strip()
        journey_date = request.form.get("journey_date", "")
        train_no = request.form.get("train_no")
        travel_class = request.form.get("travel_class")

        train = get_train(train_no) if train_no else None

        if not all([name, age, mobile, from_station, to_station, journey_date, train, travel_class]):
            flash("Please fill out all required fields.", "danger")
        elif not valid_journey_date(journey_date):
            flash("Journey date must be within 60 days from today.", "danger")
        else:
            try:
                age = int(age)
            except (TypeError, ValueError):
                flash("Please enter a valid age.", "danger")
                return render_template("book.html", trains=TRAINS)

            if age < 1 or age > 120:
                flash("Please enter a valid age between 1 and 120.", "danger")
                return render_template("book.html", trains=TRAINS)

            if train["seats"].get(travel_class, 0) <= 0:
                flash(f"No seats available in {travel_class} class.", "danger")
            else:
                train["seats"][travel_class] -= 1
                bookings = get_bookings()
                pnr = generate_pnr()
                fare = FARE_CHART[travel_class]
                booking_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

                ticket = {
                    "PNR": pnr,
                    "User": session["user_email"],
                    "Name": name,
                    "From": from_station,
                    "To": to_station,
                    "Mobile": mobile,
                    "Age": age,
                    "Nationality": nationality,
                    "Address": address,
                    "Journey Date": datetime.datetime.strptime(journey_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    "Train": train["name"],
                    "Train No": train["train_no"],
                    "Class": travel_class,
                    "Fare": fare,
                    "Departure": train["departure"],
                    "Arrival": train["arrival"],
                    "Booking Time": booking_time,
                    "Status": "CONFIRMED",
                }

                bookings[pnr] = ticket
                save_bookings(bookings)

                users = get_users()
                users[session["user_email"]]["bookings"].append(pnr)
                save_users(users)

                qr_payload = (
                    f"PNR: {pnr}\n"
                    f"Name: {name}\n"
                    f"Train: {train['name']} ({train['train_no']})\n"
                    f"From: {from_station} to {to_station}\n"
                    f"Class: {travel_class}\n"
                    f"Fare: Rs.{fare}\n"
                    f"Journey Date: {ticket['Journey Date']}\n"
                    f"Status: CONFIRMED"
                )
                qr_buffer = generate_qr_code(qr_payload)
                qr_bytes = qr_buffer.getvalue()
                qr_image = qr_to_base64(buffer=BytesIO(qr_bytes))

                try:
                    send_ticket_email(session["user_email"], ticket, qr_bytes)
                except RuntimeError as exc:
                    flash(
                        f"Ticket booked successfully, but email delivery is not configured: {exc}",
                        "warning",
                    )
                except Exception as exc:
                    app.logger.exception("Failed to send ticket email", exc_info=exc)
                    flash(
                        "Ticket booked successfully, but we could not email the ticket copy.",
                        "warning",
                    )
                else:
                    flash("Ticket booked successfully! A copy has been sent to your email.", "success")

                return render_template("ticket_success.html", ticket=ticket, qr_image=qr_image)

    return render_template("book.html", trains=TRAINS)


@app.route("/bookings")
@login_required
def view_bookings():
    bookings = get_bookings()
    users = get_users()
    user_booking_ids = users.get(session["user_email"], {}).get("bookings", [])
    user_tickets = [bookings[pnr] for pnr in user_booking_ids if pnr in bookings]
    return render_template("bookings.html", tickets=user_tickets)


@app.route("/booking/<pnr>/cancel", methods=["POST"])
@login_required
def cancel_booking(pnr):
    bookings = get_bookings()
    ticket = bookings.get(pnr)
    if not ticket or ticket["User"] != session["user_email"]:
        flash("Booking not found.", "danger")
        return redirect(url_for("view_bookings"))

    if ticket["Status"] != "CONFIRMED":
        flash("Only confirmed bookings can be cancelled.", "warning")
        return redirect(url_for("view_bookings"))

    ticket["Status"] = "CANCELLED"
    bookings[pnr] = ticket
    save_bookings(bookings)

    flash(f"Ticket cancelled. Refund amount: Rs.{ticket['Fare'] * 0.8:.0f}", "info")
    return redirect(url_for("view_bookings"))


@app.route("/booking/<pnr>/edit", methods=["GET", "POST"])
@login_required
def edit_booking(pnr):
    bookings = get_bookings()
    ticket = bookings.get(pnr)
    if not ticket or ticket["User"] != session["user_email"]:
        flash("Booking not found.", "danger")
        return redirect(url_for("view_bookings"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age")
        nationality = request.form.get("nationality", "").strip()
        address = request.form.get("address", "").strip()
        journey_date = request.form.get("journey_date", "")
        travel_class = request.form.get("travel_class")

        train = get_train(ticket["Train No"])
        if not all([name, age, nationality, address, journey_date, travel_class]):
            flash("Please fill all required fields.", "danger")
        elif not valid_journey_date(journey_date):
            flash("Journey date must be within 60 days from today.", "danger")
        else:
            try:
                age = int(age)
            except (TypeError, ValueError):
                flash("Please enter a valid age.", "danger")
                return render_template("edit_booking.html", ticket=ticket, trains=TRAINS)

            if age < 1 or age > 120:
                flash("Please enter a valid age between 1 and 120.", "danger")
                return render_template("edit_booking.html", ticket=ticket, trains=TRAINS)

            if travel_class != ticket["Class"]:
                if train["seats"].get(travel_class, 0) <= 0:
                    flash(f"No seats available in {travel_class} class.", "danger")
                    return render_template("edit_booking.html", ticket=ticket, trains=TRAINS)
                train["seats"][ticket["Class"]] += 1
                train["seats"][travel_class] -= 1

            ticket["Name"] = name
            ticket["Age"] = age
            ticket["Nationality"] = nationality
            ticket["Address"] = address
            ticket["Class"] = travel_class
            ticket["Journey Date"] = datetime.datetime.strptime(journey_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            ticket["Fare"] = FARE_CHART[travel_class]
            ticket["Booking Time"] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

            bookings[pnr] = ticket
            save_bookings(bookings)

            flash("Booking updated successfully.", "success")
            return redirect(url_for("view_bookings"))

    return render_template("edit_booking.html", ticket=ticket, trains=TRAINS)


@app.route("/pnr", methods=["GET", "POST"])
def track_pnr():
    ticket = None
    if request.method == "POST":
        pnr = request.form.get("pnr", "").strip()
        if not pnr:
            flash("Please enter a PNR number.", "danger")
        else:
            bookings = get_bookings()
            ticket = bookings.get(pnr)
            if not ticket:
                flash("PNR not found.", "danger")
            else:
                qr_payload = (
                    f"PNR: {ticket['PNR']}\n"
                    f"Name: {ticket['Name']}\n"
                    f"Train: {ticket['Train']} ({ticket['Train No']})\n"
                    f"From: {ticket['From']} to {ticket['To']}\n"
                    f"Class: {ticket['Class']}\n"
                    f"Fare: Rs.{ticket['Fare']}\n"
                    f"Journey Date: {ticket['Journey Date']}\n"
                    f"Status: {ticket['Status']}"
                )
                ticket["qr_image"] = qr_to_base64(qr_payload)

    return render_template("track_pnr.html", ticket=ticket)


@app.route("/bookings/clear", methods=["POST"])
@login_required
def clear_bookings():
    users = get_users()
    bookings = get_bookings()
    user_booking_ids = users.get(session["user_email"], {}).get("bookings", [])

    for pnr in user_booking_ids:
        bookings.pop(pnr, None)

    users[session["user_email"]]["bookings"] = []
    save_bookings(bookings)
    save_users(users)

    flash("All bookings cleared successfully.", "info")
    return redirect(url_for("view_bookings"))


if __name__ == "__main__":
    app.run(debug=True)

