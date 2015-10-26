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
    position_in_post = None# Images position out of all the images for this post, starting at 1 for the first
    html = None# Image segment HTML
    soup = None# Image segment HTML soup
    post_html = None# HTML of parent post, used for some thumbnail stuff. eurgh

    absolute_image_url = None
    server_image_filename = None
    server_image_filename_no_ext = None# For futabilly
    image_width = None
    image_height = None
    absolute_thumbnail_url = None
    thumbnail_width = None
    thumbnail_height = None
    thumbnail_filename = None
    reported_filesize = None# Sites reported filesize of full image
    image_extention = None
    uploader_filename = None
    site_filename = None
    spoilered = None# True if image is spoilered, False if not spoilered
##    md5base64_hash = None
##    sha512_hash = None
##    local_size_in_bytes = None# Locally determined size in bytes
##    local_path = None# Path to local copy of image file


    def __init__(self,post_html,image_segment_html,position_in_post):
        self.position_in_post = position_in_post
        self.post_html = post_html
        self.html = image_segment_html
        logging.debug("Image.__init__(): "+"self.html: "+repr(self.html))
        self.soup = BeautifulSoup(image_segment_html, "html5lib")# "lxml" and "html.parser" both fail on at least one /arch/ post
        return

    def find_spoiler_status(self):
        assert(self.html is not None)
        if self.spoilered is not None:# Skip extraction if we have it
            return self.spoilered
        # Find out if the image is spoilered
        # post_image_segment: <p class="fileinfo">File: <a href="/anon/src/1440564930079.png">1440564930079.png</a> <span class="morefileinfo">(Spoiler Image, 389.27 KB, 800x560, <a class="post-filename" download="1stporn.png" href="/anon/src/1440564930079.png" title="Save as original filename">1stporn.png</a>)</span></p>
        # <span class="morefileinfo">(Spoiler Image,
        self.spoilered = ("""src="/static/spoiler.png""" in self.html)
        return self.spoilered

    def find_absolute_image_link(self):
        assert(self.html is not None)
        if self.absolute_image_url is not None:# Skip extraction if we have it
            return self.absolute_image_url
        # Find location of image file
        # ex. https://www.ponychan.net/anon/src/1437401812560.jpg
        image_link = re.search("""href=["']([^"'<>"]+/src/[^"'<>"]+)["']>""", self.html, re.IGNORECASE).group(1)
        if image_link[0] == u"/":# Convert relative links to absolute
            #logging.info("Given relavtive link: "+repr(image_link))
            absolute_image_link = "https://www.ponychan.net"+image_link
        else:# If we already have an absolute link
            #logging.info("Given absolute link: "+repr(image_link))
            absolute_image_link = image_link
        #logging.debug("absolute_image_link: "+repr(absolute_image_link))
        assert(absolute_image_link[0:4]==u"http")
        self.absolute_image_url = absolute_image_link
        return self.absolute_image_url

    def find_server_image_filename(self):
        if self.server_image_filename is not None:# Skip extraction if we have it
            return self.server_image_filename
        if self.absolute_image_url is None:# We need this to figure out the filename
            find_absolute_image_link()
        # Get server filename for image
        # ex. 1437401812560.jpg
        server_image_filename = self.absolute_image_url.split("/")[-1]
        self.server_image_filename = server_image_filename
        return self.server_image_filename

    def find_server_image_filename_no_ext(self):
        if self.server_image_filename_no_ext is not None:# Skip extraction if we have it
            return self.server_image_filename_no_ext
        else:
            find_image_extention(self)# This generates the value as a side-effect
        return server_image_filename_no_ext

    def find_image_extention(self):
        if self.image_extention is not None:# Skip extraction if we have it
            return self.image_extention
        if self.server_image_filename is None:# We use this to figure out the extention
            self.find_server_image_filename()
        filename_split_search = re.search("""(.+)\.([^.]+?)$""", self.server_image_filename, re.IGNORECASE)
        self.server_image_filename_no_ext = filename_split_search.group(1)
        self.image_extention = filename_split_search.group(2)
        return self.image_extention

    def find_absolute_thumbnail_url(self):
        assert(self.html is not None)
        if self.absolute_image_url is not None:# Skip extraction if we have it
            return self.absolute_image_url

        if self.spoilered is None:# We can't figure this stuff if the image is spoilered
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
            logging.debug("Image.find_absolute_thumbnail_url(): "+"self.post_html: "+repr(self.post_html))
            thumbnail_size_search = re.search("""style=['"]width:(\d+)px;height:(\d+)px['"]""", self.post_html, re.IGNORECASE)
            self.thumbnail_width = thumbnail_size_search.group(1)
            self.thumbnail_height = thumbnail_size_search.group(2)
        return (self.thumbnail_width, self.thumbnail_height)

    def find_thumbnail_height(self):
        if self.thumbnail_height is not None:# Skip extraction if we have it
            return self.thumbnail_height
        elif self.spoilered is True:
            return None
        else:
            self.find_thumbnail_dimensions()
            return self.thumbnail_height

    def find_thumbnail_width(self):
        if self.thumbnail_width is not None:# Skip extraction if we have it
            return self.thumbnail_width
        if self.spoilered is True:
            return None
        else:
            self.find_thumbnail_dimensions()
            return self.thumbnail_width

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
        # Grab filesize and dimensions of fullsize image
        # u'(170.61 KB, 926x1205, 428261__safe_human_upvotes+gal\u2026)'
        filesize_and_dimensions_string = self.soup.find(["span"], ["morefileinfo"]).text
        # Find (reported) dimensions of image
        self.image_width, self.image_height = ponychan.parse_dimensions(filesize_and_dimensions_string)
        return (self.image_width, self.image_height)

    def find_image_width(self):
        if self.image_width is None:
            self.find_dimensions()
        return self.image_width

    def find_image_height(self):
        if self.image_height is None:
            self.find_dimensions()
        return self.image_height

##    def find_md5_base64_hash(self):
##        pass
##    def find_sha512_hash(self):
##        pass



class Post():
    """A single post"""
    position_in_thread = None# Post's position in the thread, starting at 1 for the first post
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
    post_number = None
    thread_number = None

    def __init__(self,post_html,thread_number,position_in_thread):
        # Validate input
        assert(post_html is not None)
        assert(thread_number is not None)
        assert(position_in_thread is not None)
        # Store input
        self.position_in_thread = position_in_thread
        self.thread_number = thread_number
        self.html = post_html
        logging.debug("Post.__init__(): "+"self.html: "+repr(self.html))
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

    def find_post_number(self):
        assert(self.soup is not None)
        # Get post number
        # <a class="post_no citelink" href="/anon/res/538340.html#541018">541018</a>
        post_number = int(self.soup.find(["a"], ["citelink"]).text)
        self.post_number = post_number
        return self.post_number

    def find_thread_number(self):
        assert(self.thread_number is not None)
        return self.thread_number# This is required to instantiate this class, so we don't need to calculate it

    def find_time(self):
        assert(self.html is not None)
        # Get post time
        # u"<time datetime="2013-02-16T15:51:39Z">"
        # <time\sdatetime="([\w:-]+)">
        # u"2013-02-16T15:51:39Z"
        post_time_string = re.search("""<time\sdatetime="([\w:-]+)">""", self.html, re.IGNORECASE).group(1)
        self.time = ponychan.parse_ponychan_datetime(post_time_string)
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
        position_in_post = 0
        for image_soup in image_soups:
            position_in_post += 1
            logging.debug("Post.find_images(): "+"self.html: "+repr(self.html))
            self.images.append(
                Image(
                    post_html = self.html,
                    image_segment_html = str(image_soup),
                    position_in_post = position_in_post
                    )
                )
            continue
        return self.images

    def count_images():
        if self.images is None:
            find_images(self)
        self.image_count = len(self.images)
        return self.image_count



class Thread():
    """A single thread"""
    posts = None# Array of posts for this thread
    thread_url = None
    html = None
    soup = None
##    json = None
    last_updated = None
    stickied = None
    locked = None
    thread_number = None

    def __init__(self,thread_number):
        self.thread_number = thread_number
        self.thread_url = self.generate_thread_url()
        return

    def generate_thread_url(self):
        if self.thread_url is not None:
            return self.thread_url
        else:
            self.thread_url = "https://www.ponychan.net/anon/res/"+str(self.thread_number)+".html"
            return self.thread_url

    def update(self):
        """Load the HTML for the thread and refresh the posts list"""
        html = get_url(self.thread_url)
        if html is None:# Tolerate failures
            logging.error("Filed to load thread HTML!")
            return
        self.html = html
        self.last_updated = get_current_unix_time_8chan()
        self.soup = BeautifulSoup(self.html, "html5lib")# "lxml" and "html.parser" both fail on at least one /arch/ post
        logging.debug("Updated thread HTML")
        # Refresh posts list
        self.posts = None
        self.split_posts()
        return

    def split_posts(self):
        """Split the thread into posts and instantiate Post objects for them"""
        assert(self.soup is not None)
        # Seperate posts out
        # Seperate post entries from the page HTML so we can process them seperately
        # http://stackoverflow.com/questions/5041008/handling-class-attribute-in-beautifulsoup
        post_html_segments = self.soup.findAll("div", ["postContainer","replyContainer"])
        postition_in_thread = 0
        self.posts = []
        for post_html_segment in post_html_segments:
            postition_in_thread += 1
            self.posts.append(
                Post(
                    post_html = str(post_html_segment),
                    thread_number = self.thread_number,
                    position_in_thread = postition_in_thread,
                    )
                )
            continue
        return self.posts

    def get_posts(self):
        assert(self.posts is not None)
        return self.posts



class CatalogThreadInfo():
    """Information about a thread used for update checks in catalog"""
    last_updated = None# Timestamp for last update
    thread_number = None
    reply_count = None
    position_in_catalog = None# Starting at 1 for the first
    needs_update = None# Boolean, True if an update needs to be run, False if it doesn't, None if we don't know



class Catalog():
    """A single board's catalog, not persisted outside RAM because i don't know how to do that"""
    current_version_threads = None# List of CatalogThreadInfo objects to compare for update checks
    previous_version_threads = None# List of CatalogThreadInfo objects to compare for update checks
    url = "https://www.ponychan.net/anon/catalog.html"# URL to the catalog page
    catalog_cache_path = os.path.join("cache","ponychan.pickle")
    html = None# Current catalog's HTML
    soup = None
    last_updated = None# Timestamp for last update

    def __init__(self):
        return

    def update(self):
        html = get_url(self.url)
        if html is None:# Tolerate failures
            logging.error("Filed to load thread HTML!")
            return
        self.html = html
        self.soup = None
        self.previous_version_threads = self.current_version_threads
        current_version_threads = None
        self.last_updated = get_current_unix_time_8chan()
        self.parse()
        self.run_update_check()

    def parse(self):
        """Parse thread information form the catalog"""
        # Seperate thread entries from the page HTML so we can process them seperately
        # http://stackoverflow.com/questions/5041008/handling-class-attribute-in-beautifulsoup
        self.soup = BeautifulSoup(self.html, "html.parser")
        thread_html_segments = self.soup.findAll("div", ["catathread", "catathread mature_thread"])

        self.current_version_threads = []

        thread_position_on_page = 0# First thread on the page is thread 1
        for thread_html_segment in thread_html_segments:
            thread_position_on_page += 1
            #logging.debug("thread_html_segment: "+repr(thread_html_segment))
            thread_info = CatalogThreadInfo()
            thread_info.position_in_catalog = thread_position_on_page

            # Get thread number
            catalink = thread_html_segment.find(["div","a"], ["catalink"])
            relative_link = catalink.attrs[u"href"]
            thread_number = int(re.search("""res/(\d+)""", relative_link, re.IGNORECASE).group(1))# ex. 532843
            #logging.debug("thread_number: "+repr(thread_number))
            thread_info.thread_number = thread_number

            # Get reply count for thread
            catacount = thread_html_segment.find("div", ["catacount"])
            catacount_text = catacount.get_text()
            reply_count = int(''.join(c for c in catacount_text if c.isdigit()))# ex. 12
            #logging.debug("reply_count: "+repr(reply_count))
            thread_info.reply_count = reply_count

            # Store data about this thread for processing
            thread_info.last_updated = get_current_unix_time_8chan()

            self.current_version_threads.append(thread_info)
            continue
        return

    def select_thread_info(self,thread_number,thread_info_object_list):
        assert(thread_info_object_list is not None)
        for thread_info_object in thread_info_object_list:
            if thread_info_object.thread_number == thread_number:
                return thread_info_object
        logging.debug("Thread info could not be found")
        return None

    def check_if_update_needed(self,current_version,previous_version):
        """Compare two versions of a catalog thread and see if we need to run an update for it"""
        # Was this in previous catalog?
        if previous_version is None:
            # We haven't saved this before, so save it
            return True
        # Compare the reply count
        if current_version.reply_count != previous_version.reply_count:
            logging.debug("Thread has more replies than previous catalog, triggering update. "+repr(current_version.thread_number))
            return True
        # Compare the thread position in the catalog
        if thread_position_on_page > number_of_catalog_threads - 10:
            # The thread is in the last 10 threads
            logging.debug("Thread is in the last ten threads on the catalog, triggering update. "+repr(thread_number))
            return True
        # No check triggered update, no update needed
        logging.debug("No comparison triggered an update for this thread. "+repr(thread_number))
        return False

    def run_update_check(self):
        """Compare thread info for the current version of the catalog against the previous version"""
        for current_version in self.current_version_threads:
            if self.previous_version_threads is None:
                previous_version = None
            else:
                previous_version = self.select_thread_info(
                    thread_number=current_version.thread_number,
                    thread_info_object_list=self.previous_version_threads
                    )
            current_version.needs_update = self.check_if_update_needed(current_version,previous_version)
            continue
        return

    def save_threads(self):
        """Save threads that need updating"""


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
