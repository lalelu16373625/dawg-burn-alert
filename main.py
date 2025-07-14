import requests
import time
import threading
import os
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from flask import Flask
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Einstellungen ---
TELEGRAM_BOT_TOKEN = "8159479693:AAGpluZ2zix5GpzBZMUc2XriGd1TImfxLuk"
TELEGRAM_CHAT_ID = -1002708595595  # Gruppe ID
TELEGRAM_TOPIC_ID = 145             # Topic ID für das Thread
BURN_API_URL = "https://explorer-pepu-v2-mainnet-0.t.conduit.xyz/api/v2/tokens/0x153b5ae0ff770ebe5c30b1de751d8820b2505774/transfers"
BURN_GIF_URL = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXVsZ3N5NXBkMXRzZDNobHpxOWR0bTU0cjQyejFraHJiNm00MDAzbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hgZyvKLMa429fRxkAS/giphy.gif"

BURN_ADDRESS = "0x0000000000000000000000000000000000000000"  # Burn-Adresse

# --- Globale Variable um neue burns zu tracken ---
seen_burn_ids = set()

bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

def escape_markdown(text: str) -> str:
    # Einfaches Escaping für Telegram Markdown V2, speziell für Transaction Hash im Link
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for ch in escape_chars:
        text = text.replace(ch, f"\\{ch}")
    return text

def fetch_burns():
    try:
        response = requests.get(BURN_API_URL, verify=False)
        if response.status_code == 200:
            data = response.json()
            return data.get("transfers", [])
        else:
            print(f"API Fehler: Status Code {response.status_code}")
            return []
    except Exception as e:
        print(f"Fehler bei API Abfrage: {e}")
        return []

def format_burn_message(burn, is_burn_event: bool):
    raw_value = int(burn["value"])
    raw_supply = int(burn.get("current_supply", 0))
    # In ganze Token umrechnen (Decimals = 18)
    amount = raw_value // 10**18
    current_supply = raw_supply // 10**18

    tx_hash = burn["transaction_hash"]
    timestamp_raw = burn.get("timestamp")
    try:
        timestamp_dt = datetime.strptime(timestamp_raw, "%Y-%m-%dT%H:%M:%S.%fZ")
        timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        timestamp = timestamp_raw

    flames_count = amount // 25000
    flames = "🔥" * flames_count if flames_count > 0 else ""

    header = "🔥 *New Burn Alert!* 🔥" if is_burn_event else "📤 *Transfer to Burn Address* 📤"

    tx_hash_escaped = escape_markdown(tx_hash)

    message = (
        f"{header}\n\n"
        f"Token: *DAWGZ*\n"
        f"Amount: *{amount} DAWGZ*\n"
        f"Current Supply: *{current_supply} DAWGZ*\n"
        f"Time: `{timestamp}`\n"
        f"{flames}\n\n"
        f"[View Transaction](https://explorer.pepu.io/tx/{tx_hash_escaped})"
    )
    return message

def burn_alert_loop():
    global seen_burn_ids
    print("Burn Alert Loop gestartet.")
    while True:
        burns = fetch_burns()
        for burn in burns:
            token_address = burn.get("token", {}).get("address", "").lower()
            if token_address != "0x153b5ae0ff770ebe5c30b1de751d8820b2505774":
                continue  # nur DAWGZ Token

            burn_id = burn["transaction_hash"]
            if burn_id in seen_burn_ids:
                continue

            event_type = burn.get("type", "")
            to_address = burn.get("to", {}).get("hash", "").lower()

            # Nur Burn-Events oder Transfers an Burn-Adresse
            if event_type == "token_burning" or to_address == BURN_ADDRESS.lower():
                seen_burn_ids.add(burn_id)
                is_burn_event = (event_type == "token_burning")
                msg = format_burn_message(burn, is_burn_event)
                try:
                    bot.send_animation(
                        chat_id=TELEGRAM_CHAT_ID,
                        animation=BURN_GIF_URL,
                        caption=msg,
                        parse_mode=ParseMode.MARKDOWN_V2,
                        message_thread_id=TELEGRAM_TOPIC_ID,
                        disable_web_page_preview=False
                    )
                    print(f"Nachricht gesendet für Transaction {burn_id}")
                except Exception as e:
                    print(f"Fehler beim Senden der Nachricht: {e}")
        time.sleep(30)

@app.route("/")
def home():
    return "Burn Alert Bot is running"

if __name__ == "__main__":
    t = threading.Thread(target=burn_alert_loop, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
