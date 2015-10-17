#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     17/10/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time
import re
import calendar
import logging
import logging
from utils import *


# Ponychan parsing functions
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


def parse_ponychan_datetime(time_string):
    """
    Parse ponychan's timestamp and output the equivalent in unixtime
    The Z probably stands for "zulu" A.K.A. UTC+0
    input:
        2013-02-16T15:51:39Z
    output:
        bar
    """
    #logging.debug("time_string: "+repr(time_string))
    # "2013-02-16T15:51:39Z"
    # "%Y-%m-%dT%H:%M:%SZ"
    post_time = time.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
    post_unix_time = calendar.timegm(post_time)
    #logging.debug("post_unix_time: "+repr(post_unix_time))
    return post_unix_time
# /Ponychan parsing functions



# Debug
def debug():
    """where stuff is called to debug and test"""
    print parse_ponychan_datetime(time_string="""2013-02-16T15:51:39Z""")
    return
# /Debug


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","ponychan.py-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
