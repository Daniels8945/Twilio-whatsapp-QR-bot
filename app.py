import os
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask, request, send_file
from twilio.twiml.messaging_response import MessagingResponse
import qrcode
import requests

load_dotenv()

app = Flask(__name__)

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
chat_service_sid = os.getenv("YOUR_CHAT_SERVICE_SID")
client = Client(account_sid, auth_token)

@app.route("/static/<path:filename>", methods=["GET"])
def serve_qrcode(filename):
    return send_file("static/qrcode", mimetype="image/png")


# Upload the QR code to Twilio Media API
def upload_media():

    qr_file_path = "static/qrcode.png"
    url = f"https://mcs.us1.twilio.com/v1/Services/{chat_service_sid}/Media"

    files = {
        "media": ("qrcode.png", open(qr_file_path, "rb"), "image/png")
    }
    response = requests.post(url, files=files, auth=(account_sid, auth_token))
    if response.status_code == 201:
        media_sid = response.json()["sid"]
        print(f"Media uploaded successfully. Media SID: {media_sid}")
        return media_sid
    else:
        print(f"Failed to upload media: {response.text}")
        return None


@app.route("/whatsapp", methods=["POST"])
def send_whatsapp_message():
    """Send WhatsApp message using Twilio"""
    """Get the incoming message"""

    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From")
        
    if incoming_msg.startswith("http://") or incoming_msg.startswith("https://"):
        # Generate and save QR code
        try:

            qr = qrcode.make(incoming_msg)
            qr_file = "static/qrcode.png"
            qr.save(qr_file, format="PNG")
            
            media_sid = upload_media(qr_file)
            
            if media_sid:
                response_msg = "Here's you'r QR code"
                message = client.messages.create(
                    body= response_msg,
                    from_='whatsapp:+14155238886',
                    to= sender,
                    media_url=[f"https://mcs.us1.twilio.com/v1/Services/{chat_service_sid}/Media/{media_sid}"],
                    status_callback="https://twilio-whatsapp-qr-bot.onrender.com/status-callback"
                    )
                print(f'Message sent! SID: {message.sid}')

            else: 
                     # Handle case where media upload fails
                client.messages.create(
                    from_='whatsapp:+14155238886',
                    body="Sorry, there was an error uploading your QR code. Please try again.",
                    to=sender
                )

         
        except Exception as e:
            print(f'Error sending message: {e}')
            message = client.messages.create(
                    from_='whatsapp:+14155238886',
                    body="Sorry, there was an error generating your QR code. Please try again.",
                    to=sender
                )
            # if os.path.exists(qr_file):
            #     os.remove(qr_file)


    else:
        response_msg = "Please send a link to generate a QR code."
        message = client.messages.create(
                from_='whatsapp:+14155238886',
                body=response_msg,
                to=sender

        )
    return str(MessagingResponse())

@app.route("/status-callback", methods=["POST"])
def status_callback():
    message_status = request.values.get("MessageStatus")
    print(f"Message status: {message_status}")
    return "", 200



if __name__ == "__main__":
    app.run()