#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     17/07/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy
import logging
from bs4 import BeautifulSoup# http://www.crummy.com/software/BeautifulSoup/bs4/doc/
import re

import lockfiles # MutEx lockfiles
from utils import * # General utility functions
import sql_functions# Database interaction
import config # Settings and configuration
import tables# Database table definitions



class Board:
    """Represents a board"""
    def __init__(self):
        self.catalog_url="https://www.ponychan.net/anon/catalog.html"# Absolute URL to access catalog page
        self.threads = []# List of active thread objects
        self.catalog_threads = {}# Dict of CatalogThread instances {thread_number:CatalogThread_instance,}

# Database staging classes
class StagingThread:
    """Represents a thread to be fed into the DB"""
    def __init__(self):
        self.posts = None# List of Post instances
        self.url = None# Absolute URL to access thread page
        self.thread_number = None# Number of thread from origin

class StagingPost:
    """Represents a single post from a thread"""
    def __init__(self):
        self.post_number = None# Number of post from origin
        self.images = None# List of Image instances


class StagingImage:
    """Represents any image/media associated with a post"""
    def __init__(self):
        self.uploader_filename = None# The original filename as given by the uploader (If availible)
        self.local_filename = None# Filename of the local copy of this file
        self.url = None# Absolute URL to access image
        self.md5b64_hash = None# MD5 hash of the image, stored as a base-64 string

#/Database staging classes

# Persitant RAM classes
class Catalog():
    """Represents a board's catalog page"""
    def __init__(self):
        self.threads = {}# Dict of CatalogThread instances {thread_number:CatalogThread_instance,}

class CatalogThread():
    """Represents a thread from the catalog, stores values from there so we don't have to query the DB for them"""
    def __init__(self):
        self.thread_number = None
        self.number_of_posts = None
        self.position_on_catalog_page = None
#/ Persitant RAM classes






def process_catalog(board_instance):
    """Process threads from the catalog
    https://www.ponychan.net/anon/catalog.html"""
    catalog_url = board_instance.catalog_url
    # Load catalog page
    catalog_html = get_url(catalog_url)
    if catalog_html is None:
    	logging.error("Could not load catalog: "+repr(catalog_url))
    	return
    logging.debug("catalog_html: "+repr(catalog_html))
    save_file(
    	file_path=os.path.join("debug","catalog.html"),
    	data=catalog_html,
    	force_save=True,
    	allow_fail=False)


    # Seperate thread entries from the page HTML so we can process them seperately
    # http://stackoverflow.com/questions/5041008/handling-class-attribute-in-beautifulsoup
    soup = BeautifulSoup(catalog_html, "html.parser")
    thread_html_segments = soup.findAll("div", ["catathread", "catathread mature_thread"])

    # Extract data about threads
    catalog_threads = []
    thread_position_on_page = 0# First thread on the page is thread 1
    for thread_html_segment in thread_html_segments:
        thread_position_on_page += 1
        logging.debug("thread_html_segment: "+repr(thread_html_segment))

        # Get thread number
        catalink = thread_html_segment.find(["div","a"], ["catalink"])
        relative_link = catalink.attrs[u"href"]
        thread_id = int(re.search("""res/(\d+)""", relative_link, re.IGNORECASE).group(1))# ex. 532843
        logging.debug("thread_id: "+repr(thread_id))

        # Get reply count for thread
        catacount = thread_html_segment.find("div", ["catacount"])
        catacount_text = catacount.get_text()
        reply_count = int(''.join(c for c in catacount_text if c.isdigit()))# ex. 12
        logging.debug("reply_count: "+repr(reply_count))

        # Compare new catalog data to previous catalog data
        # Make sure this thread has an entry
        if thread_id not in board_instance.catalog_threads.keys():
            board_instance.catalog_threads[thread_id] = CatalogThread()
            process_thread(board_instance,thread_id)
            continue

        # Compare the reply count
        if reply_count != board_instance.catalog_threads[thread_id].reply_count:
            process_thread(board_instance,thread_id)
            continue

        # Compare the thread position in the catalog
        #if thread_position_on_page

        continue


    return

def process_thread(board_instance, thread_id):
    """Update this thread in the DB"""
    return



def bah():
    """grab list of active threads by crawling board pages"""
    # For each board, find threads
    # Load board pages
    # Load first page
    page_url = "https://www.ponychan.net/anon/"# 1st page
    page_html = get_url(page_url)
    if page_html is None:
        logging.error("Could not load page: "+repr(page_url))
        return

    page_number = 1
    while page_number <= number_of_pages:
        page_number += 1
        # https://www.ponychan.net/anon/10.html
        page_url = "https://www.ponychan.net/anon/"+str(page_number)+".html"
        page_html = get_url(page_url)
        if page_html is None:
            logging.error("Could not load page: "+repr(page_url))
            return


def debug():
    """where stuff is called to debug and test"""
    board_instance = Board()
    process_catalog(board_instance)


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","pysagi-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
