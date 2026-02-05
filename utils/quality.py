def get_quality_emoji(ping: int) -> str:
    if ping <= 50: return "🟢"
    if ping <= 150: return "🟡"
    return "🔴"
