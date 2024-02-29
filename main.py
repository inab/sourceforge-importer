import requests
import sys
import os
import logging
import argparse
from bs4 import BeautifulSoup

from utils import push_entry, connect_db, add_metadata_to_entry


def get_entries(soup, projects):
    results = soup.find_all('div', attrs={"class":"result-heading-texts"}) # results panel
    #entries = results.find('a')
    for entry in results:
        e = entry.find('a')
        projects.append("https://sourceforge.net" + e['href'])
    return(projects)


def get_next(soup):
    URL=os.getenv('URL_SOURCEFORGE_PACKAGES', 'https://sourceforge.net/directory/bio-informatics/')
    try:
        next_href = soup.find('li', attrs={"class":"pagination-next"}).find('a')['href']
        page = next_href.split('/')[-1]
        next_url = f'{URL}{page}'
        return(next_url)
    except:
        return(None)        

def get_url(url):
    session = requests.Session()
    try:
        re = session.get(url)
    except:
        print('Impossible to make the request')
        print("problematic url: " + url)
        return(None)
    else:    
        return(re)
    
def get_soup(url):
    re = get_url(url)
    if re:
        soup = BeautifulSoup(re.text, 'html5lib')
        return(soup)
    else:
        return(None)

def get_lastUpdate(project_soup):
    last_update = project_soup.find('time', attrs={"class":"dateUpdated"})['datetime']
    return(last_update)

def get_description(project_soup):
    description = project_soup.find('p', attrs={"itemprop":"description", "class":"description"})
    #print(description)
    if description != None:
        description_plain = description.text
    else:
        description_plain = None
    return(description_plain)

def get_homepage(project_soup):
    a = project_soup.find('a', attrs={"id":"homepage"})
    if a:
        homep = a['href']
    else:
        homep = None
    #print(homep)
    return(homep)
    
def get_project_info(project_soup):
    project_info = {}
    info = project_soup.find_all('section', attrs={"class":"project-info"})
    licens = []
    project_info['license'] = []
    project_info['registered'] = False
    project_info['categories'] = []

    for section in info:
        if section.header:
            #print(section.header.h4)
            if section.header.h4.text == 'Registered':
                registered = section.section.text.strip()
                project_info['registered'] = registered

        elif section.h3:
            if section.h3.text == "License":
                for a in section.find_all("a"): 
                    licens.append(a.text)
                project_info['license'] = licens
            if section.h3.text == "Categories":
                for a in section.find_all("a"):
                    project_info['categories'].append(a.span.text)
                print(f"Categories: {project_info['categories']}")
    
    return(project_info)

def get_OS(project_soup):
    OS = []
    platforms = project_soup.find_all('div', attrs={"class":"platforms"})
    for span in platforms:
        if span.meta:
            os = span.text.strip()
            OS.append(os)
    if len(OS)>0 and OS[0]!='':
        oss = OS[0]
        opsys = oss.split('\n')
        return(opsys)


def import_data():
    try:
        ## 0.1. getting arguments
        parser = argparse.ArgumentParser(
                prog='',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument(
            "--loglevel", "-l",
            help=("Set the logging level"),
            required=False,
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            )

        arguments = parser.parse_args()
        ## 0.2. setting log level
        numeric_level = getattr(logging, arguments.loglevel.upper())

        logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - toolshed - %(message)s', stream=sys.stdout)

        logging.info("state_importation - 1")
        logging.info('connecting to database')

        # 1. connect to DB/ set files
        alambique = connect_db('alambique')

        # Go through pages and get all entries
        print( 'Getting all entries')
        session = requests.Session()
        url=os.getenv('URL_SOURCEFORGE_PACKAGES', 'https://sourceforge.net/directory/bio-informatics/')
        
        projects = []
        while url:
            re = session.get(url)
            soup = BeautifulSoup(re.text, 'html5lib')
            projects = get_entries(soup, projects)
            url = get_next(soup)
        
        logging.info(f"Number of bioinformatics linux projects in SourceForge{len(projects)}")

        if projects:
            # Extract information from each entry
            for entry in projects:
                name = entry.split('/')[-2]
                entry_all = {}
                soup = get_soup(entry)
                if soup:
                    entry_all['last_update'] = get_lastUpdate(soup)
                    entry_all['description'] = get_description(soup)
                    info = get_project_info(soup)
                    entry_all['registered'] = info["registered"]
                    entry_all['license'] = info["license"]
                    entry_all['operating_systems'] = get_OS(soup)
                    entry_all['repository'] = 'https://sourceforge.net/projects/' + name
                    entry_all['homepage'] = get_homepage(soup)
                    entry_all['name'] = name

                    identifier = f"sourceforge/{name}//"
                    tool = {
                        'data': entry_all,
                        '_id' : identifier,
                        '@data_source' : 'sourceforge',
                        '@source_url' : 'https://sourceforge.net/projects/' + name
                    }

                    document_w_metadata = add_metadata_to_entry(identifier, tool, alambique)
                    push_entry(document_w_metadata, alambique)
                    
                else:
                    logging.warning(f"error with {entry['name']} - empty")
            
        else:
            logging.exception("Exception occurred")
            logging.error('error - crucial_object_empty')
            logging.error('No projects to process. Exiting...')
            logging.info("state_importation - 2")
            exit(1)
        
    except Exception as e:
        logging.error(f'error - {type(e).__name__}')
        logging.info("state_importation - 2")
        exit(1)

    else:
        logging.info("state_importation - 0")
    

if __name__ == "__main__":
    import_data()
