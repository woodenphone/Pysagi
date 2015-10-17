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








def main():
    pass

if __name__ == '__main__':
    main()
