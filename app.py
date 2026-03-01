from flask import Flask, render_template, request, redirect
import gspread
from google.oauth2 import service_account
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import json

app = Flask(__name__)

# ---------------------------
# Google Sheets connection (Secure - from ENV)
# ---------------------------

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT"))

creds = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("tickets").sheet1


# ---------------------------
# Email Function (Secure - from ENV)
# ---------------------------


def send_email(to_email, subject, body):
    try:
        message = Mail(
            from_email=os.environ.get("EMAIL_USER"),
            to_emails=to_email,
            subject=subject,
            html_content=f"""
            <html>
                <body>
                    <h2>Support Ticket Update</h2>
                    <p>{body.replace('\n', '<br>')}</p>
                    <br>
                    <p>Regards,<br>Support Team</p>
                </body>
            </html>
            """
        )

        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        sg.send(message)

        print("Email sent successfully")

    except Exception as e:
        print("Email failed:", e)


# ---------------------------
# Generate Ticket ID
# ---------------------------

def generate_ticket_id():
    records = sheet.get_all_records()
    count = len(records) + 1
    return f"TKT-{str(count).zfill(4)}"


@app.route("/")
def home():
    return render_template("raise_ticket.html")


@app.route("/submit", methods=["POST"])
def submit_ticket():
    ticket_id = generate_ticket_id()

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    category = request.form["category"]
    subject = request.form["subject"]
    description = request.form["description"]
    priority = request.form["priority"]

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([
        ticket_id, name, email, phone, category,
        subject, description, priority,
        "Open", "", created_at, created_at
    ])

    send_email(
        email,
        f"Ticket Received - {ticket_id}",
        f"Hello {name},\n\nWe received your ticket.\nTicket ID: {ticket_id}\nSubject: {subject}\n\nThank you."
    )

    send_email(
        os.environ.get("EMAIL_USER"),
        f"New Ticket - {ticket_id}",
        f"New ticket created.\nTicket ID: {ticket_id}\nSubject: {subject}\nPriority: {priority}"
    )

    return render_template("success.html", ticket_id=ticket_id)


@app.route("/admin")
def admin():
    search_query = request.args.get("search", "").strip().lower()
    all_records = sheet.get_all_records()

    if search_query:
        records = [
            r for r in all_records
            if search_query == r["TicketID"].lower()
               or search_query == r["Email"].lower()
               or search_query in r["Subject"].lower()
               or search_query in r["Name"].lower()
        ]
    else:
        records = all_records

    total_count = len(all_records)
    open_count = len([r for r in all_records if r["Status"] == "Open"])
    inprogress_count = len([r for r in all_records if r["Status"] == "In Progress"])
    resolved_count = len([r for r in all_records if r["Status"] == "Resolved"])
    closed_count = len([r for r in all_records if r["Status"] == "Closed"])

    return render_template(
        "admin_dashboard.html",
        tickets=records,
        total=total_count,
        open_count=open_count,
        inprogress_count=inprogress_count,
        resolved_count=resolved_count,
        closed_count=closed_count,
        search_query=search_query
    )


@app.route("/update", methods=["POST"])
def update_status():
    ticket_id = request.form["ticket_id"]
    new_status = request.form["status"]

    records = sheet.get_all_records()

    for index, row in enumerate(records):
        if row["TicketID"] == ticket_id:
            sheet.update_cell(index + 2, 9, new_status)
            updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.update_cell(index + 2, 12, updated_at)

        send_email(
            row["Email"],
            f"Ticket Update - {ticket_id}",
            f"""
        Hello {row['Name']},

        Your ticket status has been updated.

        Ticket ID: {ticket_id}
        New Status: {new_status}

        Thank you.
        """
        )
        break


    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)




