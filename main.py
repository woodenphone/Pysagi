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
import ponychan
from futabilly import *
import boards


def run():
    """Run continually"""
    logging.info("Processing boards until something stops us...")
    counter = 0
    while True:
        for board_config in boards.board_settings_list:
            counter += 1
            run_once(board_config)
            continue
        logging.info("Processed all boards")
        delay(60)


def run_once(board_config):
    # Load previous run's catalog if it exists
    cached_catalog_dict = load_catalog_cache(board_config)
    if cached_catalog_dict is None:# Create empty dict if we can't get a cached catalog
        catalog_dict = {}
    else:
        catalog_dict = cached_catalog_dict
    # Read the catalog and save threads if they need it
    catalog_dict = process_catalog(
        board_config,
        old_catalog=catalog_dict
        )
    # Store the catalog data for next run
    save_catalog_cache(
        board_config,
        catalog_dict=catalog_dict
        )
    return


def process_catalog(board_config,old_catalog={}):
    """Scan catalog, decide what looks new, and update those threads.
    Takes the previous output of the function as input to remember what threads it's looked at"""
    #
    # Read catalog page
    new_catalog = read_catalog(board_config)

    # Detect what is dead
    #TODO
    # Mark dead threads as dead
    #TODO

    # Decide what to update
    threads_to_update = compare_catalog_threads(
        board_config,
        old_catalog,
        new_catalog
        )

    # Run updates
    thread_counter = 0
    for thread_to_update in threads_to_update:
        thread_counter += 1
        process_thread(board_config, thread_to_update)
        # Update date of last update to now
        new_catalog[thread_to_update]["last_updated"] = get_current_unix_time_8chan()
        continue

    # Update futabilly catalog JSON
    futabilly_save_catalog(
        board_config=board_config,
        catalog_dict=new_catalog
        )
    return new_catalog





def compare_catalog_threads(board_config,old_catalog,new_catalog):
    """compare new vs old catalog results and decide if updates are needed"""
    threads_to_update = []
    number_of_catalog_threads = len(new_catalog.keys())
    # Compare new catalog data to previous catalog data
    for thread_number in new_catalog.keys():
        current_catalog_thread = new_catalog[thread_number]
        logging.debug("current_catalog_thread: "+repr(current_catalog_thread))

        # Was this in previous catalog?
        if thread_number not in old_catalog.keys():
            logging.debug("Thread was not in previous catalog, triggering update. "+repr(thread_number))
            threads_to_update += [thread_number]
            continue

        # Compare the reply count
        elif current_catalog_thread["reply_count"] != old_catalog[thread_number]["reply_count"]:
            logging.debug("Thread has more replies than previous catalog, triggering update. "+repr(thread_number))
            threads_to_update += [thread_number]
            continue

        # Compare the thread position in the catalog
        elif thread_position_on_page > number_of_catalog_threads - 10:
            # The thread is in the last 10 threads
            logging.debug("Thread is in the last ten threads on the catalog, triggering update. "+repr(thread_number))
            threads_to_update += [thread_number]
            continue
        # Check that the output file actually exists
        elif not os.path.exists(os.path.join(config.root_path, "", thread_number+".json")):
            logging.debug("Thread is not saved on disk! triggering update. "+repr(thread_number))
            threads_to_update += [thread_number]
        # No check triggered update, no update needed
        else:
            logging.debug("No comparison triggered an update for this thread. "+repr(thread_number))
            continue
    return threads_to_update





# Catalog caching
def load_catalog_cache(board_config):
    """Read back previously outputted catalog JSON cache"""
    logging.debug("Loading catalog from cache...")
    filename = "catalog_cache.json"
    file_path = os.path.join(config.root_path, "cache", board_config["shortname"], filename)
    if not os.path.exists(file_path):
        return None
    catalog_json = read_file(file_path=file_path)
    catalog_dict = json.loads(catalog_json)
    logging.debug("Catalog loaded from cache.")
    return catalog_dict


def save_catalog_cache(board_config,catalog_dict):
    """save catalog JSON cache"""
    logging.debug("Saving cache catalog...")
    json_to_save = json.dumps(catalog_dict)
    filename = "catalog_cache.json"
    save_file(
     file_path=os.path.join(config.root_path, "cache", board_config["shortname"], filename),
    	data=json_to_save,
    	force_save=True,
    	allow_fail=False
        )
    logging.debug("Finished saving catalog cache")
    return
# /Catalog caching


# Debug
def dummy_save_images(board_config,thread_dict):
    """Pretend to save images"""
    logging.debug("Saving images...")
    thread_posts = thread_dict["thread_posts"]
    # Get all the images together in one place
    thread_images = []
    for thread_post in thread_posts:# Process images for each post
        post_images = thread_post["post_images"]
        for post_image in post_images:# Process each image for this post
            logging.debug("post_image: "+repr(post_image))
            absolute_image_link = post_image["absolute_image_link"]
            image_filename = post_image["server_image_filename"]
            image_file_path = os.path.join("images", image_filename)
            # Load image
            image_data = get_url(absolute_image_link)
            if image_data is None:
            	logging.error("Could not load image_data: "+repr(image_data))
            	continue
            save_file(
            	file_path=os.path.join("debug", image_file_path),
            	data=image_data,
            	force_save=True,
            	allow_fail=False)
            continue
    logging.debug("thread_dict: "+repr(thread_dict))
    logging.debug("Finished saving images")
    return thread_dict


def dummy_save_thread(board_config,thread_dict):
    """Pretend to save the thread"""
    logging.debug("Saving thread...")
    json_to_save = json.dumps(thread_dict)
    filename = str(thread_dict["thread_number"])+".json"
    save_file(
    	file_path=os.path.join("debug", "json_threads", filename),
    	data=json_to_save,
    	force_save=True,
    	allow_fail=False
        )
    #dummy_save_images(board_config,thread_dict)
    logging.debug("Finished saving thread")
    return


def test_futabilly_catalog_saving(board_config):
    catalog_dict = read_catalog(board_config)
    futabilly_save_catalog(board_config,catalog_dict)
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


def explore_json():
    """Debug"""
    json_data = read_file(os.path.join("notes","6404920.json"))
    json_obj = json.loads(json_data)
    logging.debug("json_obj: "+repr(json_obj))
    return


def debug():
    """where stuff is called to debug and test"""
    #run_once(board_config=boards.board_config_anon)

    process_thread(
        board_config = boards.board_config_site,
        thread_number = "243"
        )
    return
    process_catalog(
        board_config = boards.board_config_arch
        )
    return
# /Debug


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","pysagi-log.txt"))
        #run()
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
