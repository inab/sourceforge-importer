import json
import logging
import random
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SourceForgeMetadataImporter/1.0)",
    "Accept-Language": "en-US,en;q=0.9",
}

CHECKPOINT_FILE = Path("processed_sourceforge_projects.json")
CACHE_DIR = Path("cache/sourceforge")
LISTING_CACHE_DIR = CACHE_DIR / "listings"
PROJECT_CACHE_DIR = CACHE_DIR / "projects"
PROJECT_COUNT_FILE = Path("sourceforge_project_count.txt")


def create_session():
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def build_state(max_requests, min_delay, max_delay, max_consecutive_rate_limits):
    return {
        "request_count": 0,
        "max_requests": max_requests,
        "consecutive_rate_limits": 0,
        "max_consecutive_rate_limits": max_consecutive_rate_limits,
        "min_delay": min_delay,
        "max_delay": max_delay,
    }


def load_processed(resume: bool):
    if resume and CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_processed(processed):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(processed), f, indent=2)


def reset_state():
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    if PROJECT_COUNT_FILE.exists():
        PROJECT_COUNT_FILE.unlink()


def sanitize_filename(value: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in value)


def project_name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def cache_path_for_url(url: str) -> Path:
    parsed = urlparse(url)

    if "/directory/" in parsed.path:
        query = parse_qs(parsed.query)
        page = query.get("page", ["1"])[0]
        LISTING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return LISTING_CACHE_DIR / f"page_{page}.html"

    name = project_name_from_url(url) or "index"
    PROJECT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return PROJECT_CACHE_DIR / f"{sanitize_filename(name)}.html"


def read_cached_html(url: str):
    cache_file = cache_path_for_url(url)
    if cache_file.exists():
        logging.debug(f"Loading from cache: {cache_file}")
        return cache_file.read_text(encoding="utf-8")
    return None


def write_cached_html(url: str, html: str):
    cache_file = cache_path_for_url(url)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")


def write_project_count(count: int):
    PROJECT_COUNT_FILE.write_text(f"{count}\n", encoding="utf-8")


def request_with_backoff(session, url, state, max_retries=5, base_delay=10, timeout=30):
    if state["request_count"] >= state["max_requests"]:
        logging.info("Reached request budget for this run.")
        return "REQUEST_BUDGET_REACHED"

    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout)
            state["request_count"] += 1
            logging.debug(f"GET {url} -> {response.status_code} (request #{state['request_count']})")
        except requests.RequestException as e:
            sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 2)
            logging.warning(f"Request failed for {url}: {e}")
            logging.info(f"Sleeping {sleep_time:.2f}s before retry")
            time.sleep(sleep_time)
            continue

        if response.status_code == 200:
            state["consecutive_rate_limits"] = 0
            time.sleep(random.uniform(state["min_delay"], state["max_delay"]))
            return response

        if response.status_code in (429, 403, 503):
            state["consecutive_rate_limits"] += 1

            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                sleep_time = int(retry_after)
            else:
                sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 5)

            logging.warning(
                f"Received {response.status_code} for {url}. "
                f"Sleeping {sleep_time:.2f}s before retry "
                f"(attempt {attempt + 1}/{max_retries})."
            )
            time.sleep(sleep_time)

            if state["consecutive_rate_limits"] >= state["max_consecutive_rate_limits"]:
                logging.error(
                    "Too many consecutive rate-limit/protection responses "
                    f"({state['consecutive_rate_limits']}). Stopping run."
                )
                return "RATE_LIMITED"

            continue

        if response.status_code == 404:
            logging.warning(f"Received 404 for {url}")
            return None

        logging.warning(f"Unexpected status {response.status_code} for {url}")
        return None

    return None


def get_html(session, url, state, read_from_cache=True, write_to_cache=True):
    if read_from_cache:
        cached_html = read_cached_html(url)
        if cached_html is not None:
            return cached_html

    response = request_with_backoff(session, url, state)
    if response in (None, "RATE_LIMITED", "REQUEST_BUDGET_REACHED"):
        return response

    html = response.text

    if write_to_cache:
        write_cached_html(url, html)

    return html