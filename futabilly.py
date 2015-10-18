#-------------------------------------------------------------------------------
# Name:        futabilly things
# Purpose:
#
# Author:      User
#
# Created:     17/10/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from utils import *
from classes import *

# Code for Futabilly compatibility
def futabilly_save_thread(board_config,thread_number,thread_dict):
    """Output JSON for futabilly"""
    logging.debug("Saving futabilly thread...")
    json_to_save = json.dumps(thread_dict)
    filename = str(thread_number)+".json"
    save_file(
    	file_path=os.path.join("debug", "futabilly", board_config["shortname"], "res", filename),
    	data=json_to_save,
    	force_save=True,
    	allow_fail=False
        )
    logging.debug("Finished saving thread")
    return


def futabilly_save_catalog(board_config,catalog_dict):
    """Output JSON for futabilly"""
    logging.debug("Saving futabilly catalog...")
    futabilly_catalog = futabilly_format_catalog(board_config,catalog_dict)
    json_to_save = json.dumps(futabilly_catalog)
    filename = "threads.json"
    save_file(
    	file_path=os.path.join("debug", "futabilly", board_config["shortname"], filename),
    	data=json_to_save,
    	force_save=True,
    	allow_fail=False
        )
    logging.debug("Finished saving thread")
    return


def futabilly_format_catalog(board_config,catalog_dict):
    """Convert internal catalog format to 8chan style format futabilly likes"""
    threads_list = []
    thread_counter = 0
    for thread_key in catalog_dict.keys():
        thread_counter += 1
        catalog_thread = catalog_dict[thread_key]
        futabilly_thread = {
            "no":thread_key,# thread number
            "last_modified":catalog_thread["last_updated"],
            }
        threads_list += [futabilly_thread]

    futabilly_catalog = [{
        "threads":threads_list,
        "page":0,
        }]
    return futabilly_catalog
# /Code for Futabilly compatibility



# Class stuff
def dump_thread_to_futabilly(thread):
    futabilly_thread_posts = []
    for post in thread.get_posts():
        futabilly_post_images = []
        for post_image in post.find_images():
            futabilly_post_image = {# 8chan style for odillitime's futabilly.
                "absolute_media_link":post_image.find_absolute_image_link(),# Full URL to access image on server
                "absolute_thumb_link":post_image.find_absolute_thumbnail_url(),# Server thumbnail link if it exists, else None
                "ext":post_image.find_image_extention(),# Extention of image. u'ext': u'.jpg',
                "filename":post_image.find_server_image_filename_no_ext(),# Server filename without extention. u'filename': u'12',
                "fsize":post_image.find_reported_filesize(),# Size of file in bytes. u'fsize': 505901,
                "h":post_image.find_image_height(),# Height of image. u'h': 1209,
                #"md5":None,# MD5 of image, encoded in base64. u'md5': u'KDiHU3cHcwCPlIyTdROpmQ==',
                "tim":post_image.find_server_image_filename_no_ext(),# OdiliTime> tim: is the timestamp in ms (usually matches the media filename)# u'tim': u'1444463324099-1',
                "tn_h":post_image.find_thumbnail_height(),# Height of thumbnail. u'tn_h': 255,
                "tn_w":post_image.find_thumbnail_width(),# Width of thumbnail. u'tn_w': 187,
                "w":post_image.find_image_width(),# Width of image. u'w': 887},
                }
            futabilly_post_images += [futabilly_post_image]
            continue

        futabilly_thread_post = {# 8chan style for odillitime's futabilly
            "com":post.find_comment(),# OdiliTime> com: is the comment
            #"cyclical":None,# TODO
            #"id":None,# TODO
            #"last_modified":None,# TODO
            #"locked":None,# TODO
            "name":post.find_name(),# TODO
            "no":post.find_post_number(),# OdiliTime> no: is the post number
            "resto":post.find_thread_number(),# looks to be the thread number
            #"sticky":None,# TODO
            "time":post.find_time(),# OdiliTime> time: time of post
            "email":post.find_email(),# u'email': u'sage',
            "trip":post.find_tripcode(),# Tripcode
            "sub":post.find_subject(),# Title / subject
            "media":futabilly_post_images,# List/array of image info objects
            }
        logging.debug("futabilly_thread_post: "+repr(futabilly_thread_post))
        futabilly_thread_posts += [futabilly_thread_post]
        continue

    futabilly_thread_dict = {# 8chan style for odillitime's futabilly
        "posts":futabilly_thread_posts,# TODO
        }
    return futabilly_thread_dict

def process_catalog():
    catalog = Catalog()
    catalog.update()
    for catalog_thread_info in catalog.current_version_threads:
        if catalog_thread_info.needs_update:
            thread = Thread(thread_number = catalog_thread_info.thread_number)
            # Actually load the thread from the site
            thread.update()
            # Parse and save thread
            dump_thread_to_futabilly(thread)
            continue


# /Class stuff



# Debug
def debug():
    """where stuff is called to debug and test"""
    board_config_anon = {
        "catalog_page_url":"https://www.ponychan.net/anon/catalog.html",# Absolute URL to access catalog page
        "thread_url_prefix":"https://www.ponychan.net/anon/res/",# The thread url before the thread number
        "thread_url_suffix":".html",# The thread url after the thread number
        "relative_image_link_prefix":"https://www.ponychan.net",#The image link before /anon/src/1437401812560.jpg
        "relative_thumbnail_link_prefix":"https://www.ponychan.net",# #The thumbnail link before /anon/thumb/1441401127342.png
        "rescan_delay":60,# Time to pause after each cycle of scannign catalog and threads
        "shortname":"anon_class-based"
        }
    thread_number="532843"
    thread = Thread(thread_number)
    thread.update()
    thread_dict = dump_thread_to_futabilly(thread)
    futabilly_save_thread(
        board_config=board_config_anon,
        thread_number=thread_number,
        thread_dict=thread_dict
        )

    catalog = Catalog()
    catalog.update()
    catalog.parse()
    return
# /Debug



def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","futabilly.py-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
