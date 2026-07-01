
import os
import requests
from dotenv import load_dotenv

def verify_telegram_credentials():
    """
    Sends a test message to your Telegram chat to verify credentials.
    """
    load_dotenv()  # Load variables from .env file

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in your .env file.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": "Hello from your Job Finder Agent bot! Your credentials are correct."
    }

    try:
        response = requests.post(url, json=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        response_json = response.json()
        if response_json.get("ok"):
            print("[SUCCESS] A test message has been sent to your Telegram chat.")
            print("Please check your Telegram to confirm you received it.")
        else:
            print(f"[ERROR] Telegram API returned an error: {response_json.get('description')}")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to send message. An exception occurred: {e}")

if __name__ == "__main__":
    verify_telegram_credentials()
