from flask_mail import Mail, Message
import base64
from datetime import datetime

# Initialize Flask-Mail
def init_mail(app, config):
    """Initialize Flask-Mail with app and config."""
    app.config.update(
        MAIL_SERVER=config["MAIL_SERVER"],
        MAIL_PORT=config["MAIL_PORT"],
        MAIL_USE_TLS=config["MAIL_USE_TLS"],
        MAIL_USERNAME=config["MAIL_USERNAME"],
        MAIL_PASSWORD=config["MAIL_PASSWORD"],
        MAIL_DEFAULT_SENDER=config["MAIL_DEFAULT_SENDER"]
    )
    return Mail(app)

def send_email_alert(mail, detection_details, recipient_email):
    """Send an email alert with the detection details."""
    try:
        msg = Message(
            subject="Package Removal Alert",
            recipients=[recipient_email]
        )
        msg.body = f"""
        Alert: A package has been removed!

        Detection Details:
        - Type: {detection_details['type_of_detection']}
        - Confidence: {detection_details['confidence']}
        - Date: {detection_details['date']}
        - Time: {detection_details['time']}
        """
        # Attach the image if available
        if detection_details.get("image"):
            msg.attach(
                "detection_image.jpg",
                "image/jpeg",
                base64.b64decode(detection_details["image"])
            )
        mail.send(msg)
        print(f"Email sent successfully to {recipient_email}")  # Confirmation printout
    except Exception as e:
        print(f"Failed to send email: {e}")  # Log the error

def send_email_and_update_report(mail, db, detection_id, user_email, detection_details):
    """Send an email and update the detection with a report reference."""
    try:
        # Send the email
        send_email_alert(mail, detection_details, user_email)

        # Check or create a report
        report = db["Report"].find_one({"detection_id": detection_id})
        if not report: 
            report_data = {
                "detection_id": detection_id,
                "status": None,
                "timestamp": datetime.now().isoformat()
            }
            report_id = db["Report"].insert_one(report_data).inserted_id
        else:
            report_id = report["_id"]

        # Update the Detection document
        db["Detection"].update_one(
            {"detection_id": detection_id},
            {"$set": {"report_id": report_id}}
        )
        print(f"Email sent and detection {detection_id} linked to report {report_id}.")
    except Exception as e:
        print(f"Error in email-sending logic: {e}")