import requests
import time
from datetime import datetime
from telegram import Bot

# --- Telegram Einstellungen ---
TELEGRAM_BOT_TOKEN = '8159479693:AAGpluZ2zix5GpzBZMUc2XriGd1TImfxLuk'
CHAT_ID = -1002708595595  # Deine Gruppenchat-ID
TOPIC_ID = 145  # Das Topic, in dem gepostet werden soll

# --- GIF URL für den Burn Alert ---
GIF_URL = 'https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXVsZ3N5NXBkMXRzZDNobHpxOWR0bTU0cjQyejFraHJiNm00MDAzbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hgZyvKLMa429fRxkAS/giphy.gif'

# --- API URL für Burn Events ---
API_URL = 'https://explorer-pepu-v2-mainnet-0.t.conduit.xyz/api/v2/tokens/0x153b5ae0ff770ebe5c30b1de751d8820b2505774/transfers'

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Zum Tracking der schon gesendeten burns (z.B. nach tx hash)
sent_burns = set()

def fetch_burns():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return data.get('result', [])
    except Exception as e:
        print(f"Error fetching burns: {e}")
        return []

def create_fire_emojis(amount):
    # 1 🔥 per 25,000 tokens burned
    count = int(amount // 25000)
    return '🔥' * count if count > 0 else ''

def send_burn_alert(burn):
    amount = float(burn['value'])  # amount burned in DAWGZ
    current_supply = burn['current_supply']  # aktuelle supply aus API
    tx_hash = burn['transaction_hash']
    timestamp = datetime.fromtimestamp(int(burn['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')

    fire_emojis = create_fire_emojis(amount)

    message = (
        f"🔥 Burn Alert 🔥\n\n"
        f"Amount Burned: {amount:.0f} DAWGZ {fire_emojis}\n"
        f"Current Supply: {current_supply:.0f} DAWGZ\n"
        f"Timestamp: {timestamp}\n"
        f"Transaction: https://explorer.pepeunchained.com/tx/{tx_hash}"
    )

    bot.send_animation(
        chat_id=CHAT_ID,
        animation=GIF_URL,
        caption=message,
        message_thread_id=TOPIC_ID
    )

def main():
    print("Burn Alert Bot started...")
    while True:
        burns = fetch_burns()
        for burn in burns:
            tx_hash = burn['transaction_hash']
            if tx_hash not in sent_burns:
                send_burn_alert(burn)
                sent_burns.add(tx_hash)
        time.sleep(30)  # Polling alle 30 Sekunden

if __name__ == '__main__':
    main()
