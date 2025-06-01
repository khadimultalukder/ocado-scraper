import logging
import time

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("ocado_scraper.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("ocado_scraper")

def retry(func):
    def wrapper(*args, **kwargs):
        from ocado_scraper.config import RETRY_LIMIT, RETRY_DELAY
        for attempt in range(1, RETRY_LIMIT + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < RETRY_LIMIT:
                    time.sleep(RETRY_DELAY)
                else:
                    raise e
        return None
    return wrapper
