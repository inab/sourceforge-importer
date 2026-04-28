import argparse
import logging
import os
import sys

from bs4 import BeautifulSoup

from utils import push_entry, connect_db, add_metadata_to_entry
from request_utils import (
    create_session,
    build_state,
    load_processed,
    save_processed,
    reset_state,
    get_html,
    project_name_from_url,
    write_project_count,
)


def get_entries(soup, projects):
    results = soup.find_all("div", attrs={"class": "result-heading-texts"})
    for entry in results:
        e = entry.find("a")
        if e and e.get("href"):
            projects.append("https://sourceforge.net" + e["href"])
    return projects


def get_next(soup):
    base_url = os.getenv("URL_SOURCEFORGE_PACKAGES", "https://sourceforge.net/directory/bio-informatics/")
    try:
        next_href = soup.find("li", attrs={"class": "pagination-next"}).find("a")["href"]
        page = next_href.split("/")[-1]
        return f"{base_url}{page}"
    except Exception:
        return None


def get_last_update(project_soup):
    tag = project_soup.find("time", attrs={"class": "dateUpdated"})
    if tag and tag.has_attr("datetime"):
        return tag["datetime"]
    return None


def get_description(project_soup):
    description = project_soup.find("p", attrs={"itemprop": "description", "class": "description"})
    if description:
        return description.text.strip()
    return None


def get_homepage(project_soup):
    a = project_soup.find("a", attrs={"id": "homepage"})
    if a and a.has_attr("href"):
        return a["href"]
    return None


def get_project_info(project_soup):
    project_info = {
        "license": [],
        "registered": False,
        "categories": [],
    }

    info = project_soup.find_all("section", attrs={"class": "project-info"})

    for section in info:
        if section.header and section.header.h4:
            if section.header.h4.text.strip() == "Registered":
                if section.section:
                    project_info["registered"] = section.section.text.strip()

        elif section.h3:
            heading = section.h3.text.strip()
            if heading == "License":
                project_info["license"] = [a.text.strip() for a in section.find_all("a")]
            elif heading == "Categories":
                for a in section.find_all("a"):
                    if a.span:
                        project_info["categories"].append(a.span.text.strip())

    return project_info


def get_os(project_soup):
    operating_systems = []
    platforms = project_soup.find_all("div", attrs={"class": "platforms"})
    for span in platforms:
        if span.meta:
            os_text = span.text.strip()
            if os_text:
                operating_systems.append(os_text)

    if operating_systems:
        return [x.strip() for x in operating_systems[0].split("\n") if x.strip()]
    return None


def parse_args():
    parser = argparse.ArgumentParser(
        prog="",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--loglevel", "-l",
        help="Set the logging level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous checkpoint and reuse cached HTML pages."
    )

    parser.add_argument(
        "--max-requests",
        type=int,
        default=1000,
        help="Maximum number of HTTP requests to perform in this run."
    )

    parser.add_argument(
        "--min-delay",
        type=float,
        default=3.0,
        help="Minimum polite delay between successful requests (seconds)."
    )

    parser.add_argument(
        "--max-delay",
        type=float,
        default=8.0,
        help="Maximum polite delay between successful requests (seconds)."
    )

    parser.add_argument(
        "--max-consecutive-rate-limits",
        type=int,
        default=3,
        help="Stop the run after this many consecutive 429/403/503 responses."
    )

    return parser.parse_args()


def configure_logging(loglevel):
    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )


def get_soup(session, url, state, read_from_cache=True, write_to_cache=True):
    html = get_html(
        session=session,
        url=url,
        state=state,
        read_from_cache=read_from_cache,
        write_to_cache=write_to_cache,
    )
    if html in ("RATE_LIMITED", "REQUEST_BUDGET_REACHED", None):
        return html
    return BeautifulSoup(html, "html5lib")


def collect_project_urls(session, state, resume):
    url = os.getenv("URL_SOURCEFORGE_PACKAGES", "https://sourceforge.net/directory/bio-informatics/")
    projects = []

    logging.info("Getting all entries from listing pages")
    while url:
        soup = get_soup(
            session=session,
            url=url,
            state=state,
            read_from_cache=resume,
            write_to_cache=True,
        )

        if soup == "RATE_LIMITED":
            return "RATE_LIMITED", projects

        if soup == "REQUEST_BUDGET_REACHED":
            return "REQUEST_BUDGET_REACHED", projects

        if soup is None:
            logging.warning(f"Could not retrieve listing page {url}. Assuming end of pagination.")
            return "DONE", projects

        projects = get_entries(soup, projects)
        url = get_next(soup)

    return "DONE", projects


def build_tool_document(name, soup):
    info = get_project_info(soup)
    entry_all = {
        "last_update": get_last_update(soup),
        "description": get_description(soup),
        "registered": info["registered"],
        "license": info["license"],
        "operating_systems": get_os(soup),
        "repository": f"https://sourceforge.net/projects/{name}",
        "homepage": get_homepage(soup),
        "name": name,
    }

    identifier = f"sourceforge/{name}//"
    tool = {
        "data": entry_all,
        "_id": identifier,
        "@data_source": "sourceforge",
        "@source_url": f"https://sourceforge.net/projects/{name}",
    }
    return identifier, tool


def process_projects(projects, processed, session, state, alambique, resume):
    remaining_projects = [entry for entry in projects if project_name_from_url(entry) not in processed]
    logging.info(f"Already processed: {len(processed)}")
    logging.info(f"Remaining in this run: {len(remaining_projects)}")

    for entry in remaining_projects:
        name = project_name_from_url(entry)
        soup = get_soup(
            session=session,
            url=entry,
            state=state,
            read_from_cache=resume,
            write_to_cache=True,
        )

        if soup == "RATE_LIMITED":
            logging.error("Stopped due to repeated rate limiting. Progress has been saved.")
            save_processed(processed)
            return "RATE_LIMITED"

        if soup == "REQUEST_BUDGET_REACHED":
            logging.warning("Reached request budget. Saving progress and stopping cleanly.")
            save_processed(processed)
            return "REQUEST_BUDGET_REACHED"

        if soup is None:
            logging.warning(f"Could not parse project page: {entry}")
            continue

        identifier, tool = build_tool_document(name, soup)
        document_w_metadata = add_metadata_to_entry(identifier, tool, alambique)
        push_entry(document_w_metadata, alambique)

        processed.add(name)
        save_processed(processed)
        logging.info(f"Processed and saved: {name}")

    return "DONE"


def import_data():
    try:
        args = parse_args()
        configure_logging(args.loglevel)

        logging.info("state_importation - 1")
        logging.info("connecting to database")

        if not args.resume:
            logging.info("Starting fresh: removing checkpoint and cache")
            reset_state()
        else:
            logging.info("Resume mode enabled: keeping checkpoint and cache")

        processed = load_processed(args.resume)

        state = build_state(
            max_requests=args.max_requests,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_consecutive_rate_limits=args.max_consecutive_rate_limits,
        )

        alambique = connect_db("alambique")
        session = create_session()

        result, projects = collect_project_urls(
            session=session,
            state=state,
            resume=args.resume,
        )

        if result == "RATE_LIMITED":
            logging.error("Stopped while reading listing pages due to rate limiting.")
            logging.info("state_importation - 2")
            sys.exit(1)

        if result == "REQUEST_BUDGET_REACHED":
            logging.warning("Request budget reached while collecting listing pages.")
            write_project_count(len(projects))
            logging.info("state_importation - 0")
            return

        if not projects:
            logging.error("No projects were collected from SourceForge. Exiting...")
            logging.info("state_importation - 2")
            sys.exit(1)

        logging.info(f"Collected {len(projects)} project URLs from SourceForge")
        write_project_count(len(projects))

        processing_result = process_projects(
            projects=projects,
            processed=processed,
            session=session,
            state=state,
            alambique=alambique,
            resume=args.resume,
        )

        if processing_result == "RATE_LIMITED":
            logging.info("state_importation - 2")
            sys.exit(1)

        logging.info("state_importation - 0")

    except Exception as e:
        logging.exception("Exception occurred")
        logging.error(f"error - {type(e).__name__}: {e}")
        logging.info("state_importation - 2")
        sys.exit(1)


if __name__ == "__main__":
    import_data()