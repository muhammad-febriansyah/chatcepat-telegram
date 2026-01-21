import os
import asyncio
import logging
from telethon import TelegramClient, events
from app.config import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramUserbotListener:
    def __init__(self):
        self.clients = {}
        self.active_sessions = []
        
    def _get_session_path(self, session_id: str) -> str:
        """Get the session file path for a user"""
        return os.path.join(config.SESSION_PATH, f"session_{session_id}")

    async def start_session(self, session_id: str):
        """Start listening for a specific session"""
        try:
            logger.info(f"Starting listener for session: {session_id}")
            
            session_path = self._get_session_path(session_id)
            if not os.path.exists(f"{session_path}.session"):
                logger.error(f"Session file not found: {session_path}")
                return

            client = TelegramClient(session_path, config.API_ID, config.API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.warning(f"Session {session_id} is not authorized")
                return

            # Register event handler
            @client.on(events.NewMessage(incoming=True))
            async def handler(event):
                await self.handle_message(session_id, event, client)

            self.clients[session_id] = client
            self.active_sessions.append(session_id)
            
            # Keep the client running
            # In a real daemon, we wouldn't await run_until_disconnected individually like this
            # but for this proof of concept/single process manager, we need a way to manage multiple.
            # For now, let's just indicate it's started. The main loop will keep the process alive.
            logger.info(f"✅ Listener started for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to start session {session_id}: {e}")

    async def handle_message(self, session_id, event, client):
        """Handle incoming message"""
        try:
            sender = await event.get_sender()
            sender_id = sender.id
            sender_name = getattr(sender, 'first_name', 'Unknown')
            message_text = event.text
            
            logger.info(f"[{session_id}] New message from {sender_name} ({sender_id}): {message_text}")
            
            # Example Auto-Reply Logic (Simple)
            # In production, this should call Laravel API to check rules/AI
            
            # 1. Simple Keyword Match
            if "ping" in message_text.lower():
                await event.reply("Pong! 🏓 (Auto-reply from Userbot)")
                return

            # 2. Check Ongkir Shim (Example)
            if "cek ongkir" in message_text.lower():
                 await client.send_edit(await event.reply("⏳ Checking shipping cost..."), "⚠️ Maaf, fitur Cek Ongkir untuk akun pribadi sedang dalam pengembangan (memerlukan integrasi ke Laravel). Gunakan Bot resmi kami untuk fitur penuh.")
                 return

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def stop_session(self, session_id):
        """Stop listening"""
        if session_id in self.clients:
            await self.clients[session_id].disconnect()
            del self.clients[session_id]
            logger.info(f"Stopped session {session_id}")

    async def run_forever(self):
        """Main loop to keep script running"""
        # Here you would typically load all active sessions from DB/Config
        # For now, we wait indefinitely
        await asyncio.Event().wait()

# Launcher
if __name__ == "__main__":
    listener = TelegramUserbotListener()
    loop = asyncio.get_event_loop()
    
    # Example: Start a known session (you'd normally get these from argv or API)
    # loop.create_task(listener.start_session("example_session_id"))
    
    try:
        loop.run_until_complete(listener.run_forever())
    except KeyboardInterrupt:
        logger.info("Stopping listener...")
