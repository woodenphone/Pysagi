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



def run(board_config):
    """Run continually for a board"""
    catalog = {}
    counter = 0
    while True:
        counter += 1
        catalog = process_catalog(
            board_config,
            old_catalog=catalog
            )
        delay(board_config["rescan_delay"])
        continue



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
    for thread_to_update in threads_to_update:
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


def merge_catalogs(old_catalog,new_catalog):
    merged_catalog = {}
    for new_catalog_thread_key in new_catalog.keys():
        new_catalog_thread = old_catalog[new_catalog_thread_key]
        if new_catalog_thread_key not in old_catalog.keys():
            # This thread is new
            pass





def read_catalog(board_config):
    """Process threads from the catalog
    https://www.ponychan.net/anon/catalog.html"""
    catalog_url = board_config["catalog_page_url"]
    # Load catalog page
    catalog_html = get_url(catalog_url)
    if catalog_html is None:
    	logging.error("Could not load catalog: "+repr(catalog_url))
    	return
    #logging.debug("catalog_html: "+repr(catalog_html))
    save_file(
    	file_path=os.path.join("debug","catalog.html"),
    	data=catalog_html,
    	force_save=True,
    	allow_fail=False)
    logging.info("Loaded catalog")

    # Seperate thread entries from the page HTML so we can process them seperately
    # http://stackoverflow.com/questions/5041008/handling-class-attribute-in-beautifulsoup
    soup = BeautifulSoup(catalog_html, "html.parser")
    thread_html_segments = soup.findAll("div", ["catathread", "catathread mature_thread"])

    # Extract data about threads
    current_catalog_threads = {}
    thread_position_on_page = 0# First thread on the page is thread 1
    for thread_html_segment in thread_html_segments:
        thread_position_on_page += 1
        #logging.debug("thread_html_segment: "+repr(thread_html_segment))

        # Get thread number
        catalink = thread_html_segment.find(["div","a"], ["catalink"])
        relative_link = catalink.attrs[u"href"]
        thread_number = int(re.search("""res/(\d+)""", relative_link, re.IGNORECASE).group(1))# ex. 532843
        #logging.debug("thread_number: "+repr(thread_number))

        # Get reply count for thread
        catacount = thread_html_segment.find("div", ["catacount"])
        catacount_text = catacount.get_text()
        reply_count = int(''.join(c for c in catacount_text if c.isdigit()))# ex. 12
        #logging.debug("reply_count: "+repr(reply_count))

        # Store data about this thread for processing
        current_catalog_threads[thread_number] = {# TODO
            "reply_count":reply_count,# How many replies were we told the thread has?
            "thread_position_on_page":thread_position_on_page,# Where is the thread on the page, starting at 1
            "thread_number":thread_number,# Server side id for the thread
            "last_updated":None
            }
        continue
    logging.debug("current_catalog_threads: "+repr(current_catalog_threads))
    return current_catalog_threads


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
        # No check triggered update, no update needed
        else:
            logging.debug("No comparison triggered an update for this thread. "+repr(thread_number))
            continue
    return threads_to_update



def process_thread(board_config,thread_number):
    """Update this thread in the DB"""
    # Thread URL is done this way so board-level config can change more easily
    thread_url = board_config["thread_url_prefix"]+str(thread_number)+board_config["thread_url_suffix"]
    # Load thread page
    thread_html = get_url(thread_url)
    if thread_html is None:
    	logging.error("Could not load thread: "+repr(thread_url))
    	return
    #logging.debug("thread_html: "+repr(thread_html))
    save_file(
    	file_path=os.path.join("debug","thread.html"),
    	data=thread_html,
    	force_save=True,
    	allow_fail=False)
    logging.info("Loaded thread: "+repr(thread_number))

    # Seperate posts out
    # Seperate post entries from the page HTML so we can process them seperately
    # http://stackoverflow.com/questions/5041008/handling-class-attribute-in-beautifulsoup
    soup = BeautifulSoup(thread_html, "html.parser")
    post_html_segments = soup.findAll("div", ["postContainer"])
    #logging.debug("post_html_segments: "+repr(post_html_segments))

    # Detect if thread is currently stickied
    # <img class="icon" title="Sticky" src="/static/sticky.gif" alt="Sticky">
    thread_is_sticky = ("""src="/static/sticky.gif""" in thread_html)#TODO
    #logging.debug("thread_is_sticky: "+repr(thread_is_sticky))


    # Detect if thread is currently locked
    # <img class="icon" title="Locked" src="/static/locked.gif" alt="Locked">
    thread_is_locked = ("""src="/static/locked.gif""" in thread_html)#TODO
    #logging.debug("thread_is_locked: "+repr(thread_is_locked))

    # Process posts
    thread_posts = []# Staging for post data before we feed it into the DB
    futabilly_thread_posts = []# Staging for post data before we feed it into the DB
    postition_in_thread = 0
    for post_html_segment in post_html_segments:
        postition_in_thread += 1
        post_html_segment_html = post_html_segment.prettify()
        #logging.debug("post_html_segment: "+repr(post_html_segment))

        # Is post OP? (First in thread)
        # <div class="post op post_532843 post_anon-532843" id="reply_532843">
        # <div class="post op mature_post post_535762 post_anon-535762" id="reply_535762">
        post_is_op = (
            ("post op post_" in post_html_segment_html) or
            ("post op mature_post post_" in post_html_segment_html)
            )
        # If post is not OP, it should be reply, so break if it isn't
        # <div class="post reply post_532905 post_anon-532905" data-thread="532843" id="reply_532905">
        post_is_reply = (
            ("post reply post_" in post_html_segment_html) or
            ("post reply mature_post post_" in post_html_segment_html)
            )
        post_was_op_xor_reply = (post_is_op != post_is_reply)
        if not post_was_op_xor_reply:
            logging.error("Post was not OP xor reply!")
            logging.debug("locals: "+repr(locals()))
            assert(False)
        if postition_in_thread == 1:
            assert(post_is_op)# If the post is the first one in the thread but not the OP, something is probably going wrong.

        # Get post number
        # <a class="post_no citelink" href="/anon/res/538340.html#541018">541018</a>
        post_number = int(post_html_segment.find(["a"], ["citelink"]).text)
        #logging.debug("post_number: "+repr(post_number))

        # Get post time
        # u"<time datetime="2013-02-16T15:51:39Z">"
        # <time\sdatetime="([\w:-]+)">
        # u"2013-02-16T15:51:39Z"
        post_time_string = re.search("""<time\sdatetime="([\w:-]+)">""", post_html_segment_html, re.IGNORECASE).group(1)
        post_time = parse_ponychan_datetime(post_time_string)
        #logging.debug("post_time: "+repr(post_time))

        # Get post username
        post_name = post_html_segment.find(["span"], ["name"]).text
        #logging.debug("post_name: "+repr(post_name))

        # Get post text
        post_text = post_html_segment.find(["div"], ["body"]).text
        #logging.debug("post_text: "+repr(post_text))

        # Get post title (If any)
        title_search = post_html_segment.find(["span"], ["subject"])
        if title_search:
            post_title = title_search.text
        else:
            post_title = None# Represents the post having no title
        #logging.debug("post_title: "+repr(post_title))

        # Get poster email (If any)
        # u"<a class="email namepart" href="mailto:guyandsam@yahoo.com">"
        # <a\s*class="email\s*namepart"\s*href="mailto:([^"]+)">
        poster_email_search = re.search("""<a\s*class="email\s*namepart"\s*href="mailto:([^"]+)">""", post_html_segment_html, re.IGNORECASE)
        if poster_email_search:
            poster_email = poster_email_search.group(1)
        else:
            poster_email = None# Represents the post having no email address
        #logging.debug("poster_email: "+repr(poster_email))

        # Get poster tripcode (if any)
        # <span class="trip">!2EpsHX3E3s</span>
        poster_tripcode_search = post_html_segment.find(["span"], ["trip"])
        if poster_tripcode_search:
            poster_tripcode = poster_tripcode_search.text
        else:
            poster_tripcode = None# Represents the post having no email address
        #logging.debug("poster_tripcode: "+repr(poster_tripcode))


        # Find post image(s) (if any)
        post_image_segments = post_html_segment.findAll("p", ["fileinfo"])
        post_images = []# Staging for image data before we feed it into the post entry
        futabilly_post_images = []# Staging for image data before we feed it into the post entry
        image_position = 0
        for post_image_segment in post_image_segments:# Iterate through BeautifulSoup results
            image_position += 1
            #logging.debug("post_image_segment: "+repr(post_image_segment))
            post_image_segment_html = post_image_segment.prettify()
            #logging.debug("post_image_segment_html: "+repr(post_image_segment_html))


            # Find location of image file
            # ex. https://www.ponychan.net/anon/src/1437401812560.jpg
            image_link = re.search("""href=["']([^"'<>"]+/src/[^"'<>"]+)["']>""", post_image_segment_html, re.IGNORECASE).group(1)
            if image_link[0] == u"/":# Convert relative links to absolute
                #logging.info("Given relavtive link: "+repr(image_link))
                absolute_image_link = board_config["relative_image_link_prefix"]+image_link
            else:# If we already have an absolute link
                #logging.info("Given absolute link: "+repr(image_link))
                absolute_image_link = image_link
            #logging.debug("absolute_image_link: "+repr(absolute_image_link))
            assert(absolute_image_link[0:4]==u"http")

            # Get server filename for image
            # ex. 1437401812560.jpg
            server_image_filename = absolute_image_link.split("/")[-1]
            #logging.debug("server_image_filename: "+repr(server_image_filename))
            assert("/" not in server_image_filename)
            assert("." in server_image_filename)

            # Find out if the image is spoilered
            # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1440564930079.png">1440564930079.png</a> <span class="morefileinfo">(Spoiler Image, 389.27 KB, 800x560, <a class="post-filename" download="1stporn.png" href="/anon/src/1440564930079.png" title="Save as original filename">1stporn.png</a>)</span></p>
            # <span class="morefileinfo">(Spoiler Image,
            image_is_spoilered = ("""src="/static/spoiler.png""" in post_html_segment_html)
            #logging.debug("image_is_spoilered: "+repr(image_is_spoilered))

            if image_is_spoilered:
                # No thumbnail, set the vales for thumbnail stuff to None
                absolute_thumbnail_link = None
                server_thumbnail_filename = None
                thumbnail_width = None
                thumbnail_height = None
            else:# if not spoilered, grab the thumbnail stuff
                # Get thumbnail location
                # ex. https://www.ponychan.net/anon/thumb/1441401127342.png
                thumbnail_link = re.search("""src=["']([^"'<>"]+/thumb/[^"'<>"]+)["']""", post_html_segment_html, re.IGNORECASE).group(1)
                if thumbnail_link[0] == u"/":# Convert relative links to absolute
                    absolute_thumbnail_link = board_config["relative_thumbnail_link_prefix"]+thumbnail_link
                else:# If we already have an absolute link
                    absolute_thumbnail_link = thumbnail_link
                #logging.debug("absolute_thumbnail_link: "+repr(absolute_thumbnail_link))
                assert(absolute_thumbnail_link[0:4]==u"http")

                # Get server filename for thumbnail
                # ex. 1437401812560.jpg
                server_thumbnail_filename = absolute_thumbnail_link.split("/")[-1]
                #logging.debug("server_thumbnail_filename: "+repr(server_thumbnail_filename))
                assert("/" not in server_thumbnail_filename)
                assert("." in server_thumbnail_filename)

                # Get thumbnail dimensions
                # <img class="postimg" src="/anon/thumb/1435952100014.png" style="width:125px;height:103px" alt="">
                # style="width:125px;height:103px"
                # style=['"]width:(\d+)px;height:(\d+)px['"]
                # 125, 103
                thumbnail_size_search = re.search("""style=['"]width:(\d+)px;height:(\d+)px['"]""", post_html_segment_html, re.IGNORECASE)
                thumbnail_width = thumbnail_size_search.group(1)
                thumbnail_height = thumbnail_size_search.group(1)


            # Find original filename
            # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1437401812560.jpg">1437401812560.jpg</a> <span class="morefileinfo">(170.61 KB, 926x1205, <a class="post-filename" data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" download="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" href="/anon/src/1437401812560.jpg" title="Save as original filename">428261__safe_human_upvotes+gal\u2026</a>)</span></p>
            # <a class="post-filename" data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" download="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" href="/anon/src/1437401812560.jpg" title="Save as original filename">428261__safe_human_upvotes+gal\u2026</a>
            # data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png"
            # data-fn-fullname=["']([^"'<>]+)["']

            # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1441401127342.png">1441401127342.png</a> <span class="morefileinfo">(14.78 KB, 1920x1080, <a class="post-filename" download="KDDT Flag.png" href="/anon/src/1441401127342.png" title="Save as original filename">KDDT Flag.png</a>)</span></p>
            # <a class="post-filename" title="Save as original filename" href="/anon/src/1441401127342.png" download="KDDT Flag.png">KDDT Flag.png</a>
            # download="KDDT Flag.png"
            # download=["']([^"'<>]+)["']>
            original_image_filename_search = re.search("""download=["]([^"]+)["]""", post_image_segment_html, re.IGNORECASE)
            if original_image_filename_search:
                original_image_filename = original_image_filename_search.group(1)
                assert("/" not in original_image_filename)
            elif board_config["shortname"] == "arch":
                # Some threads in /arch/ don't work, so we just skip the original filename for those since they look like they don't have that
                # post_image_segment_html: u'<p class="fileinfo">\n File:\n <a href="https://ml.ponychan.net/arch/src/mtr_1377068331997.jpg">\n  mtr_1377068331997.jpg\n </a>\n <span class="morefileinfo">\n  (73.54 KB, 680x738)\n </span>\n</p>\n'
                original_image_filename = None
            else:
                # Stop if we didn't expect this special case
                logging.error("Could not grab original filename!")
                logging.debug("locals: "+repr(locals()))
                assert(False)
            #logging.debug("original_image_filename: "+repr(original_image_filename))


            # Generate filename and ext for futabilly
            futabilly_filename_split_search = re.search("""(.+).(.+?)""", post_image_segment_html, re.IGNORECASE)
            futabilly_filename = futabilly_filename_split_search.group(1)
            image_extention = futabilly_filename_split_search.group(2)
            assert("." not in image_extention)
            assert("/" not in image_extention)
            assert("\\" not in image_extention)


            # Grab filesize and dimensions of fullsize image
            # u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
            filesize_and_dimensions_string = post_image_segment.find(["span"], ["morefileinfo"]).text
            # Find (reported) filesize of image
            reported_filesize = parse_filesize(filesize_and_dimensions_string)
            #logging.debug("reported_filesize: "+repr(reported_filesize))

            # Find (reported) dimensions of image
            image_width, image_height = parse_dimensions(filesize_and_dimensions_string)
            #logging.debug("image_width: "+repr(image_width)+", image_height: "+repr(image_height))

            # Collect all data about image into once place for staging before DB stuff is done
            post_image = {#TODO
                "image_position":image_position,# Position of image in post, starting from 1
                "absolute_image_link":absolute_image_link,# Full URL to access image on server
                "server_image_filename":server_image_filename,# Server filename for image
                "image_is_spoilered":image_is_spoilered,# Boolean value of wheteher the image is spoilered (If true we don't get thumbnail)
                "absolute_thumbnail_link":absolute_thumbnail_link,# Server thumbnail link if it exists, else None
                "server_thumbnail_filename":server_thumbnail_filename,# Server thumbnail filename if it exists, else None
                "original_image_filename":original_image_filename,# Uploader's filename for the image
                "reported_filesize":reported_filesize,# Size in bytes we were told the image is (Floating point maths used here, ew)
                "image_width":image_width,# Reported width of full image
                "image_height":image_height,# Reported height of full image
                "is_op_thumb":None,# Is the thumbnail an OP thumbnail (larger)
                "local_filename":None,# Set elsewhere
                "thumbnail_width":thumbnail_width,# Width of the thumbnail, if it exists
                "thumbnail_height":thumbnail_height,# Height of the thumbnail, if it exists
                "image_extention":image_extention,# Filename after the last "."
                "futabilly_filename":None,# Filename up to the last "."
                }
            #logging.debug("post_image: "+repr(post_image))
            post_images += [post_image]

            futabilly_post_image = {# 8chan style for odillitime's futabilly.
                "absolute_image_link":absolute_image_link,# Full URL to access image on server
                "ext":image_extention,# Extention of image. u'ext': u'.jpg',
                "filename":futabilly_filename,# Server filename without extention. u'filename': u'12',
                "fsize":reported_filesize,# Size of file in bytes. u'fsize': 505901,
                "h":image_height,# Height of image. u'h': 1209,
                #"md5":None,# MD5 of image, encoded in base64. u'md5': u'KDiHU3cHcwCPlIyTdROpmQ==',
                "tim":None,# OdiliTime> tim: is the timestamp in ms (usually matches the media filename)# u'tim': u'1444463324099-1',
                "tn_h":thumbnail_height,# Height of thumbnail. u'tn_h': 255,
                "tn_w":thumbnail_width,# Width of thumbnail. u'tn_w': 187,
                "w":image_width,# Width of image. u'w': 887},
                }
            futabilly_post_images += [futabilly_post_image]

            continue

        # Collect all data about post into once place for staging before DB stuff is done
        thread_post = {#TODO
            "postition_in_thread":postition_in_thread,# Might not actually get used
            "post_is_op":post_is_op,# Boolean of whether this is the OP (first in thread)
            "post_is_reply":post_is_reply,# SHOULD be the opposite boolean value of post_is_op
            "post_number":post_number,# comment
            "post_time":post_time,# The time the post was posted, converted to unixtime
            "post_name":post_name,# Name of the poster
            "post_text":post_text,# The text/comment of the post
            "post_images":post_images,# List of image dicts
            "post_title":post_title,# The post title if it exists, else None object
            "poster_email":poster_email,# The email address given by the poster (If any), otherwise None
            "poster_tripcode":poster_tripcode,# tripcode of the post if there is one, otherwise None
            #"NONE":None,# TODO
            }
        #logging.debug("thread_post: "+repr(thread_post))
        thread_posts += [thread_post]

        futabilly_thread_post = {# 8chan style for odillitime's futabilly
            "com":post_text,# OdiliTime> com: is the comment
            #"cyclical":None,# TODO
            #"id":None,# TODO
            #"last_modified":None,# TODO
            #"locked":None,# TODO
            "name":post_name,# TODO
            "no":post_number,# OdiliTime> no: is the post number
            "resto":thread_number,# looks to be the thread number
            #"sticky":None,# TODO
            "time":post_time,# OdiliTime> time: time of post
            "email":poster_email,# u'email': u'sage',
            "trip":poster_tripcode,# Tripcode
            "sub":post_title,# Title / subject
            }
        futabilly_thread_posts += [futabilly_thread_post]

        continue

    logging.debug("thread_posts: "+repr(thread_posts))

    # Collect all the information about the thread into one place for staging
    thread_dict = {
        "thread_number":thread_number,# ID number of thread on origin server
        "thread_posts":thread_posts,# The posts in this thread
        "thread_is_sticky":thread_is_sticky,# Is the thread currently stickied?
        "thread_is_locked":thread_is_locked,# Is the thread currently locked?
        "NONE":None,# TODO
        "NONE":None,# TODO
        }

    futabilly_thread_dict = {# 8chan style for odillitime's futabilly
        "posts":futabilly_thread_posts,# TODO
        }

    # Update futabilly thread JSON
    futabilly_save_thread(
        board_config=board_config,
        thread_number=thread_number,
        thread_dict=futabilly_thread_dict
        )
    return

    dummy_save_thread(board_config,thread_dict)
    # Insert / update thread in DB
    #TODO
    return


def parse_filesize(filesize_string):
    """
    Convert *chan style filesize strings into number of bytes
    input:
        u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
        u'(29 KB, 127x160, Zombieshy-Lurk.png)'
    output:
        174704
    https://github.com/eksopl/asagi/blob/master/src/main/java/net/easymodo/asagi/YotsubaHTML.java
    """
    #logging.debug("filesize_string: "+repr(filesize_string))
    # Extract the number and unit
    filesize_search = re.search("""(\d+(?:.\d+)?)\s+(\w?b),""", filesize_string, re.IGNORECASE)
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
    input:
        u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
        u'\n  (73.54 KB, 680x738)\n </span>\n'
    output:
        (926, 1205)
    https://github.com/eksopl/asagi/blob/master/src/main/java/net/easymodo/asagi/YotsubaHTML.java
    """
    #logging.debug("dimensions_string: "+repr(dimensions_string))
    dimensions_search = re.search(""",\s?(\d+)x(\d+)""", dimensions_string, re.IGNORECASE)
    width = int(dimensions_search.group(1))
    height = int(dimensions_search.group(2))
    assert(width > 0)
    assert(height > 0)
    return (width, height)





def futabilly_save_thread(board_config,thread_number,thread_dict):
    """Output JSON for futabilly"""
    logging.debug("Saving futabilly thread...")
    json_to_save = json.dumps(thread_dict)
    filename = str(thread_number)+".json"
    save_file(
    	file_path=os.path.join("debug", "futabilly", board_config["shortname"], filename),
    	data=json_to_save,
    	force_save=True,
    	allow_fail=False
        )
    logging.debug("Finished saving thread")
    return


def futabilly_save_catalog(board_config,catalog_dict):
    """Output JSON for futabilly"""
    logging.debug("Saving futabilly catalog...")
    json_to_save = json.dumps(catalog_dict)
    filename = "catalog.json"
    save_file(
    	file_path=os.path.join("debug", "futabilly", board_config["shortname"], filename),
    	data=json_to_save,
    	force_save=True,
    	allow_fail=False
        )
    logging.debug("Finished saving thread")
    return



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
    #session = sql_functions.connect_to_db()
    #session = None#dummy
    #explore_json()
    board_config_anon = {
        "catalog_page_url":"https://www.ponychan.net/anon/catalog.html",# Absolute URL to access catalog page
        "thread_url_prefix":"https://www.ponychan.net/anon/res/",# The thread url before the thread number
        "thread_url_suffix":".html",# The thread url after the thread number
        "relative_image_link_prefix":"https://www.ponychan.net",#The image link before /anon/src/1437401812560.jpg
        "relative_thumbnail_link_prefix":"https://www.ponychan.net",# #The thumbnail link before /anon/thumb/1441401127342.png
        "rescan_delay":60,# Time to pause after each cycle of scannign catalog and threads
        "shortname":"anon"
        }
    board_config_arch = {
        "catalog_page_url":"https://www.ponychan.net/arch/catalog.html",# Absolute URL to access catalog page
        "thread_url_prefix":"https://www.ponychan.net/arch/res/",# The thread url before the thread number
        "thread_url_suffix":".html",# The thread url after the thread number
        "relative_image_link_prefix":"https://www.ponychan.net",#The image link before /anon/src/1437401812560.jpg
        "relative_thumbnail_link_prefix":"https://www.ponychan.net",# #The thumbnail link before /anon/thumb/1441401127342.png
        "rescan_delay":60,# Time to pause after each cycle of scannign catalog and threads
        "shortname":"arch"
        }

##    process_thread(
##        #session=session,
##        board_config=board_config_arch,
##        thread_number=2517907
##        )
##    process_thread(
##        #session=session,
##        board_config=board_config_arch,
##        thread_number=19588
##        )
##    return

    process_catalog(
        board_config = board_config_anon
        )
    process_catalog(
        board_config = board_config_arch
        )
    return


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
