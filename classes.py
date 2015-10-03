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
    def update_thread(self,new_catalog_thread):
        self.threads[new_catalog_thread.thread_number] = new_catalog_thread

class CatalogThread():
    """Represents a thread from the catalog, stores values from there so we don't have to query the DB for them"""
    def __init__(self,thread_id=None,number_of_posts=None,position_on_catalog_page=None):
        self.thread_number = thread_id
        self.number_of_posts = number_of_posts
        self.position_on_catalog_page = position_on_catalog_page

#/ Persitant RAM classes








def main():
    pass

if __name__ == '__main__':
    main()
