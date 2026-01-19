from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import hashlib
import hmac

from app.config import config
from app.telegram_service import telegram_service

app = FastAPI(
    title="Telegram Bot Creator Service",
    description="Service untuk auto-create Telegram Bot via BotFather",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class SendCodeRequest(BaseModel):
    session_id: str
    phone: str


class VerifyCodeRequest(BaseModel):
    session_id: str
    phone: str
    code: str
    phone_code_hash: str
    password: Optional[str] = None


class CreateBotRequest(BaseModel):
    session_id: str
    bot_name: str
    bot_username: str


class GetTokenRequest(BaseModel):
    session_id: str
    bot_username: str


class SessionRequest(BaseModel):
    session_id: str


# Auth dependency
async def verify_api_key(x_api_key: str = Header(None)):
    if not config.LARAVEL_SECRET_KEY:
        return True  # No auth if secret not set

    if not x_api_key or x_api_key != config.LARAVEL_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# Routes
@app.get("/")
async def root():
    return {
        "service": "Telegram Bot Creator",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/send-code")
async def send_code(request: SendCodeRequest, _: bool = Depends(verify_api_key)):
    """Send OTP code to phone number"""
    result = await telegram_service.send_code(
        session_id=request.session_id,
        phone=request.phone
    )
    return result


@app.post("/verify-code")
async def verify_code(request: VerifyCodeRequest, _: bool = Depends(verify_api_key)):
    """Verify OTP code and login"""
    result = await telegram_service.verify_code(
        session_id=request.session_id,
        phone=request.phone,
        code=request.code,
        phone_code_hash=request.phone_code_hash,
        password=request.password
    )
    return result


@app.post("/check-session")
async def check_session(request: SessionRequest, _: bool = Depends(verify_api_key)):
    """Check if session is still authorized"""
    result = await telegram_service.check_session(request.session_id)
    return result


@app.post("/create-bot")
async def create_bot(request: CreateBotRequest, _: bool = Depends(verify_api_key)):
    """Create a new bot via BotFather"""
    result = await telegram_service.create_bot(
        session_id=request.session_id,
        bot_name=request.bot_name,
        bot_username=request.bot_username
    )
    return result


@app.post("/get-my-bots")
async def get_my_bots(request: SessionRequest, _: bool = Depends(verify_api_key)):
    """Get list of user's bots"""
    result = await telegram_service.get_my_bots(request.session_id)
    return result


@app.post("/get-bot-token")
async def get_bot_token(request: GetTokenRequest, _: bool = Depends(verify_api_key)):
    """Get token for existing bot"""
    result = await telegram_service.get_bot_token(
        session_id=request.session_id,
        bot_username=request.bot_username
    )
    return result


@app.post("/logout")
async def logout(request: SessionRequest, _: bool = Depends(verify_api_key)):
    """Logout and remove session"""
    result = await telegram_service.logout(request.session_id)
    return result


@app.post("/delete-session")
async def delete_session(request: SessionRequest, _: bool = Depends(verify_api_key)):
    """Force delete session files (cleanup)"""
    result = await telegram_service.delete_session(request.session_id)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
