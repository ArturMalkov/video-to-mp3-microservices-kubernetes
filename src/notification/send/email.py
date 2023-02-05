import json
import os
import smtplib
from email.message import EmailMessage


def notify(message):
    try:
        message = json.loads(message)
        mp3_file_id = message["mp3_file_id"]
        sender_address = os.environ.get("GMAIL_SENDER_ADDRESS")
        sender_password = os.environ.get("GMAIL_SENDER_PASSWORD")
        recipient_address = message["username"]

        message_to_send = EmailMessage()
        message_to_send.set_content(f"mp3 file_id: {mp3_file_id} is now ready!")
        message_to_send["Subject"] = "MP3 Download"
        message_to_send["From"] = sender_address
        message_to_send["To"] = recipient_address

        # create SMTP session for sending email
        session = smtplib.SMTP("smtp.gmail.com")
        session.starttls()  # to make sure our connection to SMTP server is encrypted
        session.login(sender_address, sender_password)
        session.send_message(message_to_send, sender_address, recipient_address)
        session.quit()
        print("Mail sent")

    except Exception as err:
        print(err)
        return err
