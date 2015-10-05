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







def process_catalog(board_config,old_catalog={}):
    """Scan catalog, decide what looks new, and update those threads.
    Takes the previous output of the function as input to remember what threads it's looked at"""
    # Read catalog page
    new_catalog = read_catalog(board_config)
    # Decide what to update
    threads_to_update = compare_catalog_threads(
        board_config,
        old_catalog,
        new_catalog
        )
    # Run updates
    for thread_to_update in threads_to_update:
        process_thread(board_config, thread_id)
    return new_catalog



def read_catalog(board_config):
    """Process threads from the catalog
    https://www.ponychan.net/anon/catalog.html"""
    catalog_url=board_config[catalog_url]
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
    current_catalog_threads = {}
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

        # Store data about this thread for processing
        current_catalog_threads[thread_id] = {
            "reply_count":reply_count,
            "thread_position_on_page":thread_position_on_page,
            }
        continue
    logging.debug("current_catalog_threads: "+repr(current_catalog_threads))
    return current_catalog_threads


def compare_catalog_threads(old_catalog,new_catalog):
    """compare new vs old catalog results and decide if updates are needed"""
    threads_to_update = []
    # Compare new catalog data to previous catalog data
    for thread_id in current_catalog_threads.keys():
        current_catalog_thread = current_catalog_threads["thread_id"]
        logging.debug("current_catalog_thread: "+repr(current_catalog_thread))

        # Was this in previous catalog?
        if thread_id not in previous_catalog_threads.keys():
            logging.debug("Thread was not in previous catalog, processing. "+repr(thread_id))
            threads_to_update += thread_id
            continue

        # Compare the reply count
        elif current_catalog_thread["reply_count"] != previous_catalog_threads[thread_id]["reply_count"]:
            logging.debug("Thread has more replies than previous catalog, processing. "+repr(thread_id))
            threads_to_update += thread_id
            continue

        # Compare the thread position in the catalog
        #if thread_position_on_page
        # up
        logging.debug("No comparison triggered an update for this thread. "+repr(thread_id))
        continue
    return threads_to_update



def process_thread(board_config,thread_id):
    """Update this thread in the DB"""
    # Thread URL is done this way so board-level config can change more easily
    thread_url = board_config["thread_url_prefix"]+str(thread_id)+board_config["thread_url_suffix"]
    # Load thread page
    thread_html = get_url(thread_url)
    if thread_html is None:
    	logging.error("Could not load thread: "+repr(thread_url))
    	return
    logging.debug("thread_html: "+repr(thread_html))
    save_file(
    	file_path=os.path.join("debug","thread.html"),
    	data=thread_html,
    	force_save=True,
    	allow_fail=False)

    # Seperate posts out
    # Seperate post entries from the page HTML so we can process them seperately
    # http://stackoverflow.com/questions/5041008/handling-class-attribute-in-beautifulsoup
    soup = BeautifulSoup(thread_html, "html.parser")
    post_html_segments = soup.findAll("div", ["postContainer"])
    #logging.debug("post_html_segments: "+repr(post_html_segments))

    thread_posts = {}# Staging for post data before we feed it into the DB
    postition_in_thread = 0
    for post_html_segment in post_html_segments:
        postition_in_thread += 1
        logging.debug("post_html_segment: "+repr(post_html_segment))

        # Is post OP? (First in thread)
        # <div class="post op post_532843 post_anon-532843" id="reply_532843">
        post_is_op = ("post op post_" in post_html_segment.prettify())
        # If post is not OP, it should be reply, so break if it isn't
        # <div class="post reply post_532905 post_anon-532905" data-thread="532843" id="reply_532905">
        post_is_reply = ("post reply post_" in post_html_segment.prettify())
        post_was_op_xor_reply = (post_is_op != post_is_reply)
        if not post_was_op_xor_reply:
            logging.debug("locals: "+repr(locals()))
            assert(False)

        # Get post number
        # <a class="post_no citelink" href="/anon/res/538340.html#541018">541018</a>
        post_number = int(post_html_segment.find(["a"], ["citelink"]).text)
        logging.debug("post_number: "+repr(post_number))

        # Get post time
        post_time_string = post_html_segment.find(["time"]).text
        logging.debug("post_time_string: "+repr(post_time_string))
        #TODO convert to unix time

        # Get post username
        post_name = post_html_segment.find(["span"], ["name"]).text
        logging.debug("post_name: "+repr(post_name))

        # Get post text
        post_text = post_html_segment.find(["div"], ["body"]).text
        logging.debug("post_text: "+repr(post_text))

        # Find post image(s) (if any)
        post_image_segments = post_html_segment.findAll("p", ["fileinfo"])
        post_images = []# Staging for image data before we feed it into the post entry
        image_position = 0
        for post_image_segment in post_image_segments:# Iterate through BeautifulSoup results
            image_position += 1
            post_image_segment_html = post_image_segment.prettify()
            logging.debug("post_image_segment: "+repr(post_image_segment))

            # Find location of image file
            # ex. https://www.ponychan.net/anon/src/1437401812560.jpg
            image_link = re.search("""href=["']([^"'<>"]+/src/[^"'<>"]+)["']>""", post_image_segment_html, re.IGNORECASE).group(1)
            if image_link[0] == u"/":# Convert relative links to absolute
                absolute_image_link = board_config["relative_image_link_prefix"]+image_link
            else:# If we already have an absolute link
                absolute_image_link = image_link
            logging.debug("absolute_image_link: "+repr(absolute_image_link))
            assert(absolute_image_link[0:4]==u"http")

            # Get server filename for image
            # ex. 1437401812560.jpg
            server_image_filename = absolute_image_link.split("/")[-1]
            logging.debug("server_image_filename: "+repr(server_image_filename))
            assert("/" not in server_image_filename)
            assert("." in server_image_filename)

            # Find out if the image is spoilered
            image_is_spoilered = ("""src="/static/spoiler.png""" in post_image_segment_html)
            logging.debug("image_is_spoilered: "+repr(image_is_spoilered))

            if image_is_spoilered:
                absolute_thumbnail_link = None
                server_thumbnail_filename = None
            else:# if not spoilered, grab the thumbnail stuff
                # Get thumbnail location
                # ex. https://www.ponychan.net/anon/thumb/1441401127342.png
                thumbnail_link = re.search("""href=["']([^"'<>"]+/thumb/[^"'<>"]+)["']>""", post_image_segment_html, re.IGNORECASE).group(1)
                if thumbnail_link[0] == u"/":# Convert relative links to absolute
                    absolute_thumbnail_link = board_config["relative_thumbnail_link_prefix"]+thumbnail_link
                else:# If we already have an absolute link
                    absolute_thumbnail_link = thumbnail_link
                logging.debug("absolute_thumbnail_link: "+repr(absolute_thumbnail_link))
                assert(absolute_thumbnail_link[0:4]==u"http")

                # Get server filename for thumbnail
                # ex. 1437401812560.jpg
                server_thumbnail_filename = absolute_thumbnail_link.split("/")[-1]
                logging.debug("server_thumbnail_filename: "+repr(server_thumbnail_filename))
                assert("/" not in server_thumbnail_filename)
                assert("." in server_thumbnail_filename)

            # Find original filename
            # <a class="post-filename" data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" download="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" href="/anon/src/1437401812560.jpg" title="Save as original filename">428261__safe_human_upvotes+gal\u2026</a>
            # data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png"
            original_image_filename = re.search("""data-fn-fullname=["']([^"'<>]+)["']""", post_image_segment_html, re.IGNORECASE).group(1)
            logging.debug("original_image_filename: "+repr(original_image_filename))
            assert("/" not in original_image_filename)
            assert("." in original_image_filename)

            # Grab filesize and dimensions of fullsize image
            # u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
            filesize_and_dimensions_string = post_image_segment_html.find(["span"], ["morefileinfo"]).text
            # Find (reported) filesize of image
            reported_filesize = parse_filesize(filesize_and_dimensions_string)
            logging.debug("reported_filesize: "+repr(reported_filesize))

            # Find (reported) dimensions of image
            dimensions_string = filesize_and_dimensions_string.split(",")[1]# u" 926x1205"
            image_width, image_height = parse_dimensions(dimensions_string)
            logging.debug("image_width: "+repr(image_width)+", image_height: "+repr(image_height))

            # Collect all data about image into once place for staging before DB stuff is done
            post_image = {#TODO
                "image_position":image_position,# Position of image in post, starting from 1
                }
            post_images += post_image
            continue

        # Collect all data about post into once place for staging before DB stuff is done
        thread_post = {#TODO
            "":"",#
            }
        thread_posts += thread_post
        continue


    # Insert / update thread in DB
    #TODO

    return


def parse_filesize(filesize_string):
    """
    Convert *chan style filesize strings into number of bytes
    input: u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
    output: 174704
    https://github.com/eksopl/asagi/blob/master/src/main/java/net/easymodo/asagi/YotsubaHTML.java
    """
    # Extract the number and unit
    filesize_search = re.search("""(\d+.\d+)\s+(\w?b),""", filesize_string, re.IGNORECASE)
    number_string = filesize_search.group(1)# u"170.61"
    unit_string = filesize_search.group(2).lower()# u"kb" OR u"b" OR u"mb"
    unmultiplied_size = float(number_string)
    # Multiply by the unit and return value
    if unit_string == "b":# Bytes
        return int(unmultiplied_size)
    elif unit_string == "kb":# Kilobytes
        return int(unmultiplied_size * 1024)
    elif unit_string == "mb":# Megabytes
        return int(unmultiplied_size * 1024 * 1024)
    # Deal with invalid input
    logging.error("Could not parse filesize!")
    logging.debug("locals(): "+repr(locals()))
    raise ValueError


def parse_dimensions(dimensions_string):
    """
    Convert *chan style dimensions strings into integers for height and width
    input: u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
    output: (926, 1205)
    https://github.com/eksopl/asagi/blob/master/src/main/java/net/easymodo/asagi/YotsubaHTML.java
    """
    dimensions_search = re.search(""",\s?(\d+)x(\d+),""", dimensions_string, re.IGNORECASE)
    width = int(dimensions_search.group(1))
    height = int(dimensions_search.group(2))
    assert(width > 0)
    assert(height > 0)
    return (width, height)




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

    board_config = {
        "catalog_page_url":"https://www.ponychan.net/anon/catalog.html",# Absolute URL to access catalog page
        "thread_url_prefix":"https://www.ponychan.net/anon/res/",# The thread url before the thread number
        "thread_url_suffix":".html",# The thread url after the thread number
        "relative_image_link_prefix":"https://www.ponychan.net",#The image link before /anon/src/1437401812560.jpg
        "relative_thumbnail_link_prefix":"https://www.ponychan.net",# #The thumbnail link before /anon/thumb/1441401127342.png
        }
    process_thread(
        board_config,
        thread_id=532843
        )

    process_catalog(
        board_config = board_config
        )


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
