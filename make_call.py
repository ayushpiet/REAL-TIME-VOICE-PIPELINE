import os
from twilio.rest import Client
from dotenv import load_dotenv

def place_test_call():
    # Load variables from .env
    load_dotenv()
    
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_number = os.environ['TWILIO_PHONE_NUMBER']
    
    # We use your ngrok URL combined with the webhook route
    webhook_url = f"{os.environ['PUBLIC_BASE_URL'].rstrip('/')}/inbound-call"
    
    # Initialize Twilio Client
    client = Client(account_sid, auth_token)

    print(f"Initiating call from {twilio_number} to +917082968702...")
    print(f"Webhook URL being used: {webhook_url}")

    # Trigger the call
    call = client.calls.create(
        to='+917082968702',
        from_=twilio_number,
        url=webhook_url
    )
    
    print(f"✅ Call placed successfully! Your phone should be ringing.")
    print(f"Call SID: {call.sid}")

if __name__ == "__main__":
    place_test_call()
