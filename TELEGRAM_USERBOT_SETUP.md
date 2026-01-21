# 🤖 Telegram Userbot Listener Setup

This guide explains how to set up and run the **Telegram Userbot Listener**, which enables auto-reply features for **Personal Telegram Accounts** (not just Bots).

## 📋 Prerequisites

1. Python 3.9+
2. Dependencies installed via `applications/python/telegram-service/requirements.txt`
3. A logged-in session (created via the Laravel Dashboard -> Connect Telegram)

## 🚀 Running the Service

The Userbot logic runs as a **background process** separately from the main Telegram Service API.

### 1. Start the Service

Navigate to the Python service directory:

```bash
cd applications/python/telegram-service
source venv/bin/activate  # Activate virtual environment
```

Run the API service (which now manages the listener):

```bash
python3 app/main.py
```

This will start the service on `http://localhost:8001`.

### 2. How it Works

1.  **Dashboard Integration**: When you connect a Telegram account in the Laravel Dashboard, it creates a session file.
2.  **Start Listening**: To enable auto-reply for that account, the Laravel backend sends a POST request to `http://localhost:8001/listener/start`.
3.  **Background Task**: The Python service starts a background `TelegramClient` listener for that session.
4.  **Auto-Reply**: The listener detects incoming messages and triggers the auto-reply logic defined in `app/telegram_listener.py`.

## 🛠️ Configuration & Customization

The auto-reply logic is located in `applications/python/telegram-service/app/telegram_listener.py`.

Currently implemented features in Userbot:
- **Ping/Pong**: Reply "Pong!" to "ping"
- **Cek Ongkir Placeholder**: Replies with a development message (full integration pending Laravel API call)

### Extending Logic

To add more complex logic, edit the `handle_message` function in `telegram_listener.py`:

```python
async def handle_message(self, session_id, event, client):
    text = event.text.lower()
    
    # Example: Reply to "halo"
    if "halo" in text:
        await event.reply("Halo juga! Ada yang bisa dibantu?")
```

## ⚠️ Important Notes

-   **Persistence**: If you restart the Python service, all active listeners will be stopped. You need to restart them (currently manual or requires a Laravel scheduled job to re-sync).
-   **Security**: Ensure your `api_id` and `api_hash` in `config.py` are kept secret.
