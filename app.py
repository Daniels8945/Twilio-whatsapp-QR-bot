import os
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask, request, send_file
from twilio.twiml.messaging_response import MessagingResponse
import qrcode

load_dotenv()

app = Flask(__name__)

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)


@app.route("/static/<path:filename>", methods=["GET"])
def serve_qrcode(filename):
    return send_file("static/qrcode", mimetype="image/png")


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
            
            response_msg = "Here's you'r QR code"
            message = client.messages.create(
                body= response_msg,
                from_='whatsapp:+14155238886',
                to= sender,
                media_url=["https://twilio-whatsapp-qr-bot.onrender.com/static/qrcode.png"],
                status_callback="https://twilio-whatsapp-qr-bot.onrender.com/status-callback"
                )
            print(f'Message sent! SID: {message.sid}')

         
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
        # response = MessagingResponse()
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