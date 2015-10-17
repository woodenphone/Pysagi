#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     03/10/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import logging
from bs4 import BeautifulSoup# http://www.crummy.com/software/BeautifulSoup/bs4/doc/
import re

from utils import *
import config


import ponychan

class Image():
    """A single image"""
    html = None# Image segment HTML
    soup = None# Image segment HTML soup

    absolute_url = None
    image_width = None
    image_height = None

    absolute_thumbnail_url = None
    thumbnail_width = None
    thumbnail_height = None
    thumbnail_filename = None

##    md5base64_hash = None
##    sha512_hash = None
##    local_size_in_bytes = None# Locally determined size in bytes
    reported_filesize = None# Sites reported filesize of full image

    extention = None
    uploader_filename = None
    site_filename = None
    spoilered = None# True if image is spoilered, False if not spoilered
    local_path = None# Path to local copy of image file

    def __init__(self,image_segment_html):
        self.html = image_segment_html
        self.soup = BeautifulSoup(image_segment_html, "html5lib")# "lxml" and "html.parser" both fail on at least one /arch/ post
        return

    def find_spoiler_status(self):
        assert(self.html is not None)
        # Find out if the image is spoilered
        # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1440564930079.png">1440564930079.png</a> <span class="morefileinfo">(Spoiler Image, 389.27 KB, 800x560, <a class="post-filename" download="1stporn.png" href="/anon/src/1440564930079.png" title="Save as original filename">1stporn.png</a>)</span></p>
        # <span class="morefileinfo">(Spoiler Image,
        self.spoilered = ("""src="/static/spoiler.png""" in self.html)
        return self.spoilered

    def find_thumbnail_url(self):
        assert(self.html is not None)
        if self.spoilered is None:
            self.find_spoiler_status()

        if self.spoilered:
            self.absolute_thumbnail_url = None
        else:
            # If not spoilered, grab the thumbnail stuff
            # Get thumbnail location
            # ex. https://www.ponychan.net/anon/thumb/1441401127342.png
            thumbnail_link = re.search("""src=["']([^"'<>"]+/thumb/[^"'<>"]+)["']""", self.html, re.IGNORECASE).group(1)
            if thumbnail_link[0] == u"/":# Convert relative links to absolute
                absolute_thumbnail_link = board_config["relative_thumbnail_link_prefix"]+thumbnail_link
            else:# If we already have an absolute link
                absolute_thumbnail_link = thumbnail_link
            assert(absolute_thumbnail_link[0:4]==u"http")
            self.absolute_thumbnail_url = absolute_thumbnail_link

        return self.absolute_thumbnail_url

    def find_thumbnail_dimensions(self):
        assert(self.html is not None)
        if self.spoilered is None:
            self.find_spoiler_status()

        if self.spoilered:
            self.thumbnail_width = None
            self.thumbnail_height = None
        else:
            thumbnail_size_search = re.search("""style=['"]width:(\d+)px;height:(\d+)px['"]""", self.html, re.IGNORECASE)
            self.thumbnail_width = thumbnail_size_search.group(1)
            self.thumbnail_height = thumbnail_size_search.group(2)
        return (self.thumbnail_width, self.thumbnail_height)

    def find_uploader_filename(self):
        assert(self.html is not None)
        # Find original filename
        # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1437401812560.jpg">1437401812560.jpg</a> <span class="morefileinfo">(170.61 KB, 926x1205, <a class="post-filename" data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" download="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" href="/anon/src/1437401812560.jpg" title="Save as original filename">428261__safe_human_upvotes+gal\u2026</a>)</span></p>
        # <a class="post-filename" data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" download="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png" href="/anon/src/1437401812560.jpg" title="Save as original filename">428261__safe_human_upvotes+gal\u2026</a>
        # data-fn-fullname="428261__safe_human_upvotes+galore_crying_lyra+heartstrings_sad_hug_artist-colon-aymint.png"
        # data-fn-fullname=["']([^"'<>]+)["']

        # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1441401127342.png">1441401127342.png</a> <span class="morefileinfo">(14.78 KB, 1920x1080, <a class="post-filename" download="KDDT Flag.png" href="/anon/src/1441401127342.png" title="Save as original filename">KDDT Flag.png</a>)</span></p>
        # <a class="post-filename" title="Save as original filename" href="/anon/src/1441401127342.png" download="KDDT Flag.png">KDDT Flag.png</a>
        # download="KDDT Flag.png"
        # download=["']([^"'<>]+)["']>
        original_image_filename_search = re.search("""download=["]([^"]+)["]""", self.html, re.IGNORECASE)
        if original_image_filename_search:
            original_image_filename = original_image_filename_search.group(1)
            assert("/" not in original_image_filename)
            # Ensure we got the original filename
            original_image_filename_split_search = re.search("""(.+)\.([^.]+?)$""", original_image_filename, re.IGNORECASE)
            if not original_image_filename_split_search:
                logging.error("Original filename could not be split into name/ext")
                original_image_filename = None
                assert(False)

        elif """href="https://ml.ponychan.net/arch/src/""" in self.html:
            # Some threads in /arch/ don't work, so we just skip the original filename for those since they look like they don't have that
            # post_image_segment_html: u'<p class="fileinfo">\n File:\n <a href="https://ml.ponychan.net/arch/src/mtr_1377068331997.jpg">\n  mtr_1377068331997.jpg\n </a>\n <span class="morefileinfo">\n  (73.54 KB, 680x738)\n </span>\n</p>\n'
            original_image_filename = None
        else:
            # Stop if we didn't expect this special case
            logging.error("Could not grab original filename!")
            logging.debug("locals: "+repr(locals()))
            assert(False)
        #logging.debug("original_image_filename: "+repr(original_image_filename))
        self.uploader_filename = original_image_filename
        return self.uploader_filename

    def find_reported_filesize(self):
        # Grab filesize and dimensions of fullsize image
        # u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
        filesize_and_dimensions_string = self.soup.find(["span"], ["morefileinfo"]).text
        # Find (reported) filesize of image
        reported_filesize = ponychan.parse_filesize(filesize_and_dimensions_string)
        self.reported_filesize = reported_filesize
        return self.reported_filesize

    def find_dimensions(self):
        filesize_and_dimensions_string = self.soup.find(["span"], ["morefileinfo"]).text
        # Find (reported) dimensions of image
        self.image_width, self.image_height = ponychan.parse_dimensions(filesize_and_dimensions_string)
        return self.image_width, self.image_height

##    def find_md5_base64_hash(self):
##        pass
##    def find_sha512_hash(self):
##        pass









class Post():
    """A single post"""
    html = None
    json = None
    soup = None
    is_op = None# If True post is OP, if False post is reply
    time = None
    images = None# Array of images this post has
    image_count = None# Number of images
    comment = None
    name = None
    tripcode = None
    email = None
    number = None

    def __init__(self,post_html):
        assert(post_html is not None)
        self.html = post_html
        self.soup = BeautifulSoup(post_html, "html5lib")# "lxml" and "html.parser" both fail on at least one /arch/ post
        assert(self.soup is not None)
        return

    def find_op_status(self):
        assert(self.html is not None)
        # Is post OP? (First in thread)
        # <div class="post op post_532843 post_anon-532843" id="reply_532843">
        # <div class="post op mature_post post_535762 post_anon-535762" id="reply_535762">
        post_is_op = (
            ("post op post_" in self.html) or
            ("post op mature_post post_" in self.html)
            )
        # If post is not OP, it should be reply, so break if it isn't
        # <div class="post reply post_532905 post_anon-532905" data-thread="532843" id="reply_532905">
        post_is_reply = (
            ("post reply post_" in self.html) or
            ("post reply mature_post post_" in self.html)
            )
        assert(post_is_op != post_is_reply)# Post should be either OP xor reply, not both or neither
        self.is_op = post_is_op
        return self.is_op

    def find_time(self):
        assert(self.html is not None)
        # Get post time
        # u"<time datetime="2013-02-16T15:51:39Z">"
        # <time\sdatetime="([\w:-]+)">
        # u"2013-02-16T15:51:39Z"
        post_time_string = re.search("""<time\sdatetime="([\w:-]+)">""", self.html, re.IGNORECASE).group(1)
        self.time = parse_ponychan_datetime(post_time_string)
        return self.time

    def find_name(self):
        assert(self.soup is not None)
        # Get post username
        self.name = self.soup.find(["span"], ["name"]).text
        return self.name

    def find_tripcode(self):
        assert(self.soup is not None)
        # Get poster tripcode (if any)
        # <span class="trip">!2EpsHX3E3s</span>
        tripcode_search = self.soup.find(["span"], ["trip"])
        if tripcode_search:
            self.tripcode = tripcode_search.text
        else:
            self.tripcode = None# Represents the post having no email address
        return self.tripcode

    def find_comment(self):
        """Get post text"""
        assert(self.soup is not None)
        self.comment = self.soup.find(["div"], ["body"]).text
        return self.comment

    def find_subject(self):
        """Get post title (If any)"""
        assert(self.soup is not None)
        title_search = self.soup.find(["span"], ["subject"])
        if title_search:
            self.title = title_search.text
        else:
            self.title = None# Represents the post having no title
        return self.title

    def find_email(self):
        """Get poster email (If any)"""
        assert(self.soup is not None)
        # u"<a class="email namepart" href="mailto:guyandsam@yahoo.com">"
        # <a\s*class="email\s*namepart"\s*href="mailto:([^"]+)">
        poster_email_search = re.search("""<a\s*class="email\s*namepart"\s*href="mailto:([^"]+)">""", self.html, re.IGNORECASE)
        if poster_email_search:
            self.email = poster_email_search.group(1)
        else:
            self.email = None# Represents the post having no email address
        return self.email

    def find_images(self):
        assert(self.soup is not None)
        image_soups = self.soup.findAll("p", ["fileinfo"])
        self.images = []
        for image_soup in image_soups:
            self.images.append( Image(image_html = image_soup.prettify()) )
        return self.images

    def count_images():
        if self.images is None:
            find_images(self)
        self.image_count = len(self.images)
        return self.images






class Thread():
    """A single thread"""
    posts = None# Array of posts for this thread
    url = None
    html = None
##    json = None
    last_updated = None
    stickied = None
    locked = None
    number = None

    def update(self):
        pass
    def split_posts(self):
        pass



class Catalog():
    """A single board's catalog"""
    threads = None
    url = None
    last_updated = None

    def update(self):
        pass



class Board():
    """A single Board"""
    catalog = None
    threads = None




class Site():
    """A site"""
    boards = None




def main():
    pass

if __name__ == '__main__':
    main()
