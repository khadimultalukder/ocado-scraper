from ocado_scraper.scraper import run_scraper, save_csv
from ocado_scraper.utils import setup_logger

def load_skus(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Failed to load SKUs: {e}")
        return []

if __name__ == "__main__":
    log = setup_logger()
    sku_list = load_skus("sku_list.txt")
    if sku_list:
        results = run_scraper(sku_list, log)
        save_csv(results, "ocado_full_output.csv", log)
        log.info("All tasks complete.")
