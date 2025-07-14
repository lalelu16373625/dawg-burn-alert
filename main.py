import requests
import time
import threading
import os
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from flask import Flask

# --- Einstellungen (hier änderst du deine Tokens & IDs) ---
TELEGRAM_BOT_TOKEN = "8159479693:AAGpluZ2zix5GpzBZMUc2XriGd1TImfxLuk"
TELEGRAM_CHAT_ID = -1002708595595  # Gruppe ID
TELEGRAM_TOPIC_ID = 145             # Topic ID für das Thread
BURN_API_URL = "https://explorer-pepu-v2-mainnet-0.t.conduit.xyz/api/v2/tokens/0x153b5ae0ff770ebe5c30b1de751d8820b2505774/transfers"
BURN_GIF_URL = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXVsZ3N5NXBkMXRzZDNobHpxOWR0bTU0cjQyejFraHJiNm00MDAzbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hgZyvKLMa429fRxkAS/giphy.gif"

# --- Globale Variable um neue burns zu tracken ---
seen_burn_ids = set()

bot = Bot(token=TELEGRAM_BOT_TOKEN)

app = Flask(__name__)

def fetch_burns():
    try:
        response = requests.get(BURN_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get("transfers", [])
        else:
            print(f"API Fehler: Status Code {response.status_code}")
            return []
    except Exception as e:
        print(f"Fehler bei API Abfrage: {e}")
        return []

def format_burn_message(burn):
    # Werte aus der API
    amount = float(burn["value"])  # Menge token burned (z.B. 25000)
    current_supply = float(burn["current_supply"])  # Aktuelle Supply nach Burn
    tx_hash = burn["transaction_hash"]
    timestamp = datetime.fromtimestamp(burn["timestamp"]).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Anzahl der Flammen: 1🔥 pro 25.000 token burned
    flames_count = int(amount // 25000)
    flames = "🔥" * flames_count

    message = (
        f"🔥 *New Burn Alert!* 🔥\n\n"
        f"Amount Burned: *{amount:,.0f} DAWGZ*\n"
        f"Current Supply: *{current_supply:,.0f} DAWGZ*\n"
        f"Time: `{timestamp}`\n"
        f"{flames}\n\n"
        f"[View Transaction](https://explorer.pepu.io/tx/{tx_hash})"
    )
    return message

def burn_alert_loop():
    global seen_burn_ids
    print("Burn Alert Loop gestartet.")
    while True:
        burns = fetch_burns()
        for burn in burns:
            burn_id = burn["transaction_hash"]
            if burn_id not in seen_burn_ids:
                seen_burn_ids.add(burn_id)
                msg = format_burn_message(burn)
                try:
                    bot.send_animation(
                        chat_id=TELEGRAM_CHAT_ID,
                        animation=BURN_GIF_URL,
                        caption=msg,
                        parse_mode=ParseMode.MARKDOWN_V2,
                        message_thread_id=TELEGRAM_TOPIC_ID,
                        disable_web_page_preview=False
                    )
                    print(f"Nachricht gesendet für Burn {burn_id}")
                except Exception as e:
                    print(f"Fehler beim Senden der Nachricht: {e}")
        time.sleep(30)

@app.route("/")
def home():
    return "Burn Alert Bot is running"

if __name__ == "__main__":
    # Bot Loop in Thread starten
    t = threading.Thread(target=burn_alert_loop, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
