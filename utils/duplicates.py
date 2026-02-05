from database.mongo import db

def is_duplicate(link: str) -> bool:
    return db.configs.find_one({"full_link": link}) is not None
