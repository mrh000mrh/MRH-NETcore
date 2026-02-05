from telegram import Bot
from config import CHANNELS, BATCH_SIZE, BATCH_INTERVAL
from formatter.message_formatter import format_config_message
from utils.qr_generator import generate_qr_bytes
import asyncio

async def send_batch_configs(configs: list[dict]):
    for i in range(0, len(configs), BATCH_SIZE):
        batch = configs[i:i + BATCH_SIZE]
        for cfg in batch:
            text, reply_markup = format_config_message(cfg)
            for channel in CHANNELS:
                await Bot.send_message(
                    chat_id=channel,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        await asyncio.sleep(BATCH_INTERVAL)

async def send_single_config(cfg: dict):
    text, reply_markup = format_config_message(cfg)
    for channel in CHANNELS:
        await Bot.send_message(
            chat_id=channel,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
