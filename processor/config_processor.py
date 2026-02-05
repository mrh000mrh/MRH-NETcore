from parser.html_parser import parse_telegram_export
from utils.duplicates import is_duplicate
from utils.location import get_location_flag
from utils.quality import get_quality_emoji
from database.mongo import db
import hashlib

async def process_html_file(file_bytes: bytes, submitted_by: str = None) -> list[dict]:
    raw_configs = parse_telegram_export(file_bytes)
    processed = []

    for cfg in raw_configs:
        link = cfg["full_link"]
        if is_duplicate(link):
            continue

        unique_id = hashlib.md5(link.encode()).hexdigest()[:12]
        location = cfg["location"]  # بعداً ipinfo واقعی اضافه شود
        cfg.update({
            "unique_id": unique_id,
            "location_flag": get_location_flag(location),
            "quality_emoji": get_quality_emoji(cfg["ping"]),
            "remark": f"MRH-NETcore | @{submitted_by}" if submitted_by else cfg["remark"],
            "submitted_by": submitted_by
        })
        processed.append(cfg)
        db.configs.insert_one(cfg)  # ذخیره نهایی

    return processed
