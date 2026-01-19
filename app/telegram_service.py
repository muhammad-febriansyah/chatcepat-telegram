import os
import re
import asyncio
from typing import Optional, Tuple
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from telethon.tl.types import User
from app.config import config


class TelegramService:
    """Service for managing Telegram sessions and creating bots via BotFather"""

    def __init__(self):
        self.clients: dict[str, TelegramClient] = {}
        self.pending_codes: dict[str, asyncio.Future] = {}

    def _get_session_path(self, session_id: str) -> str:
        """Get the session file path for a user"""
        os.makedirs(config.SESSION_PATH, exist_ok=True)
        return os.path.join(config.SESSION_PATH, f"session_{session_id}")

    async def _get_or_create_client(self, session_id: str) -> TelegramClient:
        """Get existing client or create a new one"""
        if session_id in self.clients:
            client = self.clients[session_id]
            if client.is_connected():
                return client

        session_path = self._get_session_path(session_id)
        client = TelegramClient(session_path, config.API_ID, config.API_HASH)
        self.clients[session_id] = client

        if not client.is_connected():
            await client.connect()

        return client

    async def send_code(self, session_id: str, phone: str) -> dict:
        """Send verification code to phone number"""
        try:
            client = await self._get_or_create_client(session_id)

            # Send code request
            sent_code = await client.send_code_request(phone)

            return {
                "success": True,
                "phone_code_hash": sent_code.phone_code_hash,
                "message": "Kode verifikasi telah dikirim ke Telegram Anda"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Gagal mengirim kode: {str(e)}"
            }

    async def verify_code(self, session_id: str, phone: str, code: str, phone_code_hash: str, password: Optional[str] = None) -> dict:
        """Verify the code and login"""
        try:
            client = await self._get_or_create_client(session_id)

            try:
                # Try to sign in with code
                user = await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            except SessionPasswordNeededError:
                # 2FA is enabled
                if not password:
                    return {
                        "success": False,
                        "requires_2fa": True,
                        "message": "Akun memiliki 2FA, masukkan password"
                    }
                user = await client.sign_in(password=password)

            if isinstance(user, User):
                return {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "phone": user.phone
                    },
                    "message": "Login berhasil!"
                }

            return {
                "success": False,
                "message": "Login gagal"
            }

        except PhoneCodeInvalidError:
            return {
                "success": False,
                "error": "invalid_code",
                "message": "Kode verifikasi salah"
            }
        except PhoneCodeExpiredError:
            return {
                "success": False,
                "error": "expired_code",
                "message": "Kode verifikasi sudah expired, silakan minta kode baru"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Gagal verifikasi: {str(e)}"
            }

    async def check_session(self, session_id: str) -> dict:
        """Check if session is still valid"""
        try:
            client = await self._get_or_create_client(session_id)

            if await client.is_user_authorized():
                me = await client.get_me()
                return {
                    "success": True,
                    "authorized": True,
                    "user": {
                        "id": me.id,
                        "first_name": me.first_name,
                        "last_name": me.last_name,
                        "username": me.username,
                        "phone": me.phone
                    }
                }

            return {
                "success": True,
                "authorized": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def create_bot(self, session_id: str, bot_name: str, bot_username: str) -> dict:
        """Create a new bot via BotFather"""
        try:
            client = await self._get_or_create_client(session_id)

            if not await client.is_user_authorized():
                return {
                    "success": False,
                    "error": "not_authorized",
                    "message": "Session tidak valid, silakan login ulang"
                }

            # Get BotFather entity
            botfather = await client.get_entity("@BotFather")

            # Send /newbot command
            await client.send_message(botfather, "/newbot")
            await asyncio.sleep(1.5)

            # Send bot name
            await client.send_message(botfather, bot_name)
            await asyncio.sleep(1.5)

            # Send bot username
            if not bot_username.endswith("bot") and not bot_username.endswith("Bot"):
                bot_username = bot_username + "_bot"

            await client.send_message(botfather, bot_username)
            await asyncio.sleep(2)

            # Get last messages from BotFather
            messages = await client.get_messages(botfather, limit=3)

            # Parse token from response
            token = None
            for msg in messages:
                if msg.text:
                    # Look for token pattern: 123456789:ABCdefGHI...
                    match = re.search(r'(\d+:[A-Za-z0-9_-]+)', msg.text)
                    if match:
                        token = match.group(1)
                        break

            if token:
                # Extract bot info from token
                bot_id = token.split(":")[0]

                return {
                    "success": True,
                    "bot": {
                        "token": token,
                        "bot_id": bot_id,
                        "username": bot_username,
                        "name": bot_name
                    },
                    "message": f"Bot @{bot_username} berhasil dibuat!"
                }
            else:
                # Check if there's an error message
                last_message = messages[0].text if messages else ""

                if "already taken" in last_message.lower() or "sudah digunakan" in last_message.lower():
                    return {
                        "success": False,
                        "error": "username_taken",
                        "message": f"Username @{bot_username} sudah digunakan, coba username lain"
                    }

                return {
                    "success": False,
                    "error": "token_not_found",
                    "message": "Gagal membuat bot, coba lagi",
                    "last_response": last_message
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Gagal membuat bot: {str(e)}"
            }

    async def get_my_bots(self, session_id: str) -> dict:
        """Get list of user's bots from BotFather"""
        try:
            client = await self._get_or_create_client(session_id)

            if not await client.is_user_authorized():
                return {
                    "success": False,
                    "error": "not_authorized",
                    "message": "Session tidak valid"
                }

            botfather = await client.get_entity("@BotFather")

            # Send /mybots command
            await client.send_message(botfather, "/mybots")
            await asyncio.sleep(2)

            # Get response
            messages = await client.get_messages(botfather, limit=1)

            if messages:
                return {
                    "success": True,
                    "response": messages[0].text
                }

            return {
                "success": False,
                "message": "Tidak ada response dari BotFather"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_bot_token(self, session_id: str, bot_username: str) -> dict:
        """Get token for an existing bot"""
        try:
            client = await self._get_or_create_client(session_id)

            if not await client.is_user_authorized():
                return {
                    "success": False,
                    "error": "not_authorized",
                    "message": "Session tidak valid"
                }

            botfather = await client.get_entity("@BotFather")

            # Send /token command
            await client.send_message(botfather, "/token")
            await asyncio.sleep(1.5)

            # Select the bot
            await client.send_message(botfather, f"@{bot_username}")
            await asyncio.sleep(2)

            # Get response
            messages = await client.get_messages(botfather, limit=1)

            if messages and messages[0].text:
                match = re.search(r'(\d+:[A-Za-z0-9_-]+)', messages[0].text)
                if match:
                    return {
                        "success": True,
                        "token": match.group(1)
                    }

            return {
                "success": False,
                "message": "Token tidak ditemukan"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def logout(self, session_id: str) -> dict:
        """Logout and remove session"""
        try:
            # Disconnect and logout client
            if session_id in self.clients:
                client = self.clients[session_id]
                try:
                    if client.is_connected():
                        await client.log_out()
                        await client.disconnect()
                except:
                    pass
                del self.clients[session_id]

            # Remove all session files
            session_path = self._get_session_path(session_id)
            self._delete_session_files(session_path)

            return {
                "success": True,
                "message": "Logout berhasil, session dihapus"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _delete_session_files(self, session_path: str) -> None:
        """Delete all session related files"""
        import glob

        # Possible session file extensions
        extensions = ['', '.session', '.session-journal']

        for ext in extensions:
            file_path = f"{session_path}{ext}"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

        # Also try glob pattern for any related files
        for file in glob.glob(f"{session_path}*"):
            try:
                os.remove(file)
            except:
                pass

    async def delete_session(self, session_id: str) -> dict:
        """Force delete session without logout (for cleanup)"""
        try:
            # Disconnect client if exists
            if session_id in self.clients:
                client = self.clients[session_id]
                try:
                    if client.is_connected():
                        await client.disconnect()
                except:
                    pass
                del self.clients[session_id]

            # Remove session files
            session_path = self._get_session_path(session_id)
            self._delete_session_files(session_path)

            return {
                "success": True,
                "message": "Session dihapus"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
telegram_service = TelegramService()
