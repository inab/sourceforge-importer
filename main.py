import requests
import sys
import os
import logging
import argparse
import time
import random
from bs4 import BeautifulSoup

from utils import push_entry, connect_db, add_metadata_to_entry


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SourceForgeMetadataImporter/1.0; +your_email_or_project_url)",
    "Accept-Language": "en-US,en;q=0.9",
}


def create_session():
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def get_url(session, url, max_retries=5, base_delay=2, timeout=20):
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout)
        except requests.RequestException as e:
            logging.warning(f"Request failed for {url}: {e}")
            sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logging.info(f"Sleeping {sleep_time:.2f}s before retry")
            time.sleep(sleep_time)
            continue

        if response.status_code == 200:
            # small polite delay even on success
            time.sleep(random.uniform(1.0, 2.5))
            return response

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    sleep_time = int(retry_after)
                except ValueError:
                    sleep_time = base_delay * (2 ** attempt)
            else:
                sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)

            logging.warning(f"429 Too Many Requests for {url}. Sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
            continue

        if response.status_code >= 500:
            sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logging.warning(f"Server error {response.status_code} for {url}. Sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
            continue

        logging.warning(f"Unexpected status {response.status_code} for {url}")
        return None

    logging.error(f"Max retries exceeded for {url}")
    return None


def get_soup(session, url):
    response = get_url(session, url)
    if response is not None:
        return BeautifulSoup(response.text, "html5lib")
    return None


def get_entries(soup, projects):
    results = soup.find_all('div', attrs={"class": "result-heading-texts"})
    for entry in results:
        e = entry.find('a')
        if e and e.get('href'):
            projects.append("https://sourceforge.net" + e['href'])
    return projects


def get_next(soup):
    URL = os.getenv('URL_SOURCEFORGE_PACKAGES', 'https://sourceforge.net/directory/bio-informatics/')
    try:
        next_href = soup.find('li', attrs={"class": "pagination-next"}).find('a')['href']
        page = next_href.split('/')[-1]
        next_url = f'{URL}{page}'
        return next_url
    except Exception:
        return None


def get_lastUpdate(project_soup):
    tag = project_soup.find('time', attrs={"class": "dateUpdated"})
    return tag['datetime'] if tag and tag.has_attr('datetime') else None


def get_description(project_soup):
    description = project_soup.find('p', attrs={"itemprop": "description", "class": "description"})
    return description.text.strip() if description else None


def get_homepage(project_soup):
    a = project_soup.find('a', attrs={"id": "homepage"})
    return a['href'] if a and a.has_attr('href') else None


def get_project_info(project_soup):
    project_info = {
        'license': [],
        'registered': False,
        'categories': []
    }

    info = project_soup.find_all('section', attrs={"class": "project-info"})

    for section in info:
        if section.header and section.header.h4:
            if section.header.h4.text.strip() == 'Registered':
                if section.section:
                    project_info['registered'] = section.section.text.strip()

        elif section.h3:
            heading = section.h3.text.strip()
            if heading == "License":
                project_info['license'] = [a.text.strip() for a in section.find_all("a")]
            elif heading == "Categories":
                for a in section.find_all("a"):
                    if a.span:
                        project_info['categories'].append(a.span.text.strip())

    return project_info


def get_OS(project_soup):
    OS = []
    platforms = project_soup.find_all('div', attrs={"class": "platforms"})
    for span in platforms:
        if span.meta:
            os_text = span.text.strip()
            if os_text:
                OS.append(os_text)

    if OS:
        return OS[0].split('\n')
    return None


def import_data():
    try:
        parser = argparse.ArgumentParser(
            prog='',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        parser.add_argument(
            "--loglevel", "-l",
            help="Set the logging level",
            required=False,
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )

        arguments = parser.parse_args()
        numeric_level = getattr(logging, arguments.loglevel.upper())

        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )

        logging.info("state_importation - 1")
        logging.info('connecting to database')

        alambique = connect_db('alambique')
        session = create_session()

        logging.info('Getting all entries')
        url = os.getenv('URL_SOURCEFORGE_PACKAGES', 'https://sourceforge.net/directory/bio-informatics/')

        projects = []
        while url:
            response = get_url(session, url)
            if response is None:
                logging.warning(f"Could not retrieve page: {url}")
                break

            soup = BeautifulSoup(response.text, 'html5lib')
            projects = get_entries(soup, projects)
            url = get_next(soup)

        logging.info(f"Number of bioinformatics linux projects in SourceForge: {len(projects)}")

        if not projects:
            logging.error('No projects to process. Exiting...')
            logging.info("state_importation - 2")
            sys.exit(1)

        for entry in projects:
            name = entry.rstrip('/').split('/')[-1]
            soup = get_soup(session, entry)

            if soup:
                info = get_project_info(soup)
                entry_all = {
                    'last_update': get_lastUpdate(soup),
                    'description': get_description(soup),
                    'registered': info["registered"],
                    'license': info["license"],
                    'operating_systems': get_OS(soup),
                    'repository': f'https://sourceforge.net/projects/{name}',
                    'homepage': get_homepage(soup),
                    'name': name
                }

                identifier = f"sourceforge/{name}//"
                tool = {
                    'data': entry_all,
                    '_id': identifier,
                    '@data_source': 'sourceforge',
                    '@source_url': f'https://sourceforge.net/projects/{name}'
                }

                document_w_metadata = add_metadata_to_entry(identifier, tool, alambique)
                push_entry(document_w_metadata, alambique)
            else:
                logging.warning(f"Could not parse project page: {entry}")

    except Exception as e:
        logging.exception("Exception occurred")
        logging.error(f'error - {type(e).__name__}')
        logging.info("state_importation - 2")
        sys.exit(1)

    else:
        logging.info("state_importation - 0")


if __name__ == "__main__":
    import_data()