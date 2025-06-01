import requests
import csv
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from ocado_scraper.config import *
from ocado_scraper.utils import retry

@retry
def fetch_product_api_data(sku):
    url = f"https://www.ocado.com/webshop/api/v1/products?skus={sku}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    if res.status_code == 200:
        data = res.json()
        return data[0] if data else None
    raise Exception(f"API failed with {res.status_code}")

@retry
def fetch_image_url(url):
    res = requests.head(url, timeout=5)
    return url if res.status_code == 200 else ""

def fetch_product_images(sku):
    prefix = sku[:3]
    return {
        f"Image_{i + 1}": fetch_image_url(f"https://www.ocado.com/productImages/{prefix}/{sku}_{i}_640x640.jpg")
        for i in range(IMAGE_COUNT)
    }

@retry
def fetch_product_html_section(sku):
    url = f"https://www.ocado.com/products/{sku}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, "html.parser")
        section = soup.find("section", class_="bop-section bop-productInformation")
        return section.decode_contents() if section else ""
    raise Exception(f"Page failed with {res.status_code}")

def build_entry(sku, index, total, log):
    try:
        data = fetch_product_api_data(sku)
        if not data:
            log.warning(f"[{index}/{total}] Skipped SKU: {sku}")
            return None

        entry = {
            "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
            "shop_name": "Ocado",
            "shop_id": "ocado.com",
            "shop_country": "UK",
            "shop_language": "en",
            "shop_currency": "GBP",
            "shop_product_id": sku,
            "Product_URL": f"https://www.ocado.com/products/{sku}",
            "category_path": data.get("mainCategory", ""),
            "cat1": "", "cat2": "", "cat3": "", "cat4": "", "cat5": "",
            "Brand": data.get("brand", {}).get("name", ""),
            "Name": data.get("name", ""),
            "Price": data.get("price", {}).get("current", ""),
            "Qty_Range": "", "Min_Qty": "", "Max_Qty": "",
            **fetch_product_images(sku),
            "product_description1": fetch_product_html_section(sku),
        }

        for i in range(2, DESCRIPTION_COUNT + 1):
            entry[f"product_description{i}"] = ""

        for i in range(1, 11):
            entry[f"others{i}"] = ""

        log.info(f"[{index}/{total}] Finished SKU: {sku}")
        return entry
    except Exception as e:
        log.error(f"[{index}/{total}] Failed SKU {sku}: {e}")
        return None

def run_scraper(sku_list, log):
    total = len(sku_list)
    index_map = {sku: i + 1 for i, sku in enumerate(sku_list)}
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(build_entry, sku, index_map[sku], total, log): sku for sku in sku_list}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    log.info("====== SCRAPE SUMMARY ======")
    log.info(f"Total SKUs       : {total}")
    log.info(f"Successfully done: {len(results)}")
    log.info(f"Failed/skipped   : {total - len(results)}")
    log.info("============================")
    return results

def save_csv(data, filename, log):
    if not data:
        log.warning("No data to save.")
        return

    fieldnames = list(data[0].keys())
    try:
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        log.info(f"Saved {len(data)} records to {filename}")
    except Exception as e:
        log.error(f"Error saving CSV: {e}")
