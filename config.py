import os
from dotenv import load_dotenv
from typing import List

load_dotenv("/etc/secrets/secrets.env")   # مسیر Render Secret File

BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""
ADMIN_ID: int = int(os.getenv("ADMIN_ID") or "0")
MONGODB_URI: str = os.getenv("MONGODB_URI") or ""
IPINFO_TOKEN: str = os.getenv("IPINFO_TOKEN", "")

CHANNELS: List[str] = [
    ch.strip() for ch in (os.getenv("CHANNELS") or "@mrhnetcore").split(",")
]

SEND_CLIENTS_AFTER_STATS: bool = os.getenv("SEND_CLIENTS", "true").lower() == "true"
APPROVAL_MODE: bool = os.getenv("APPROVAL_MODE", "false").lower() == "true"
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "8"))
BATCH_INTERVAL: int = int(os.getenv("BATCH_INTERVAL", "150"))  # ثانیه

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID is required")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI is required for production")
