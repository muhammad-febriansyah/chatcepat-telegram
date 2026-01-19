# Telegram Bot Creator Service

Service Python untuk auto-create Telegram Bot via BotFather menggunakan Telethon (MTProto).

## Setup

### 1. Get Telegram API Credentials

1. Buka https://my.telegram.org
2. Login dengan nomor telepon Telegram
3. Klik "API development tools"
4. Buat aplikasi baru
5. Catat `api_id` dan `api_hash`

### 2. Install Dependencies

```bash
cd /applications/python/telegram-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
LARAVEL_SECRET_KEY=your_secret_key
```

### 4. Run Service

```bash
python run.py
```

Service akan berjalan di `http://localhost:8001`

## API Endpoints

### POST /send-code
Kirim OTP ke nomor telepon
```json
{
  "session_id": "unique_session_id",
  "phone": "+6281234567890"
}
```

### POST /verify-code
Verifikasi OTP dan login
```json
{
  "session_id": "unique_session_id",
  "phone": "+6281234567890",
  "code": "12345",
  "phone_code_hash": "hash_from_send_code",
  "password": "optional_2fa_password"
}
```

### POST /create-bot
Buat bot baru via BotFather
```json
{
  "session_id": "unique_session_id",
  "bot_name": "My Awesome Bot",
  "bot_username": "my_awesome_bot"
}
```

### POST /check-session
Cek status session
```json
{
  "session_id": "unique_session_id"
}
```

### POST /logout
Logout dan hapus session
```json
{
  "session_id": "unique_session_id"
}
```

## Flow Integrasi Laravel

```
1. User masukkan phone number
2. Laravel call POST /send-code
3. User terima OTP di Telegram
4. User input OTP
5. Laravel call POST /verify-code
6. User input nama bot & username
7. Laravel call POST /create-bot
8. Service return token
9. Laravel simpan token ke database
```

## Security Notes

- Selalu set `LARAVEL_SECRET_KEY` di production
- Session files disimpan di folder `sessions/`
- Jangan share session files
# chatcepat-telegram
