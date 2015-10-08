#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     04/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import sqlalchemy# Database  library
from sqlalchemy.ext.declarative import declarative_base# Magic for ORM

from utils import *
import config # User specific settings
from tables import *# Table definitions


# General
def connect_to_db():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    engine = sqlalchemy.create_engine(config.sqlalchemy_login, echo=config.echo_sql)
    # Bind the engine to the metadata of the Base class so that the
    # declaratives can be accessed through a DBSession instance
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
    # A DBSession() instance establishes all conversations with the database
    # and represents a "staging zone" for all the objects loaded into the
    # database session object. Any change made against the objects in the
    # session won't be persisted into the database until you call
    # session.commit(). If you're not happy about the changes, you can
    # revert all of them back to the last commit by calling
    # session.rollback()
    session = DBSession()

    logging.debug("Session connected to DB")
    return session


# Media
def check_if_hash_in_db(session,sha512base16_hash):
    """Check if a hash is in the media DB
    Return a dict of the first found row if it is, otherwise return None"""
    hash_query = sqlalchemy.select([Media]).where(Media.sha512base16_hash == sha512base16_hash)
    hash_rows = session.execute(hash_query)
    hash_row = hash_rows.fetchone()
    if hash_row:
        return hash_row
    else:
        return None


def check_if_media_url_in_DB(session,media_url):
    """Check if a URL is in the media DB
    Return a dict of the first found row if it is, otherwise return None"""
    media_url_query = sqlalchemy.select([Media]).where(Media.media_url == media_url)
    media_url_rows = session.execute(media_url_query)
    media_url_row = media_url_rows.fetchone()
    if media_url_row:
        return media_url_row
    else:
        return None
# /Media

# Boards
def get_board_id(session,board_shortname):
    try:
        board_id_query = sqlalchemy.select([Boards.board_id]).where(Boards.board_shortname == board_shortname)
        blog_id_rows = session.execute(blog_id_query)
        blog_id_row = blog_id_rows.fetchone()
        if blog_id_row:
            board_id = blog_id_row["board_id"]
            logging.debug("board_id: "+repr(board_id))
            return board_id
        else:
            # If board is not in DB, create a record for it and return the ID
            # Create entry
            board_dict = {}
            board_dict["board_shortname"] = board_shortname
            boards_row = Boards(**board_dict)
            session.add(boards_row)
            session.commit()

            # Return board entry
            return get_board_id(session,blog_url)
    except err:
        session.rollback()# Prevent DB damage
        logging.exception(err)
        raise# Propogate the exception so we can't ignore it
# /Boards

# Posts

def get_thread_id(session,board_config,thread_dict):
    """Get the ID for a thread's row, creating it if needed"""
    try:
        existing_thread_query = sqlalchemy.select([Threads]).\
            where(Threads.thread_number == thread_dict["thread_number"])
        existing_thread_rows = session.execute(existing_thread_query)
        existing_thread_row = existing_thread_rows.fetchone()
        if thread_row is None:
            # Create the thread row
            new_threads_row_dict = {}
            new_threads_row_dict["thread_number"] = thread_dict["thread_number"]
            new_threads_row_dict["thread_number"] = thread_dict["thread_number"]

            new_threads_row = posts(**new_threads_row_dict)
            session.add(new_threads_row)
            session.flush()
            thread_id = new_threads_row.thread_id
        else:
            # Grab ID from existing row
            thread_id = existing_thread_row.thread_id
        return thread_id
    except err:
        session.rollback()# Prevent DB damage
        logging.exception(err)
        raise# Propogate the exception so we can't ignore it


def insert_thread(session,board_config,thread_dict):
    """Insert or update a thread of posts and images into the DB"""
    try:
        # Check if thread is in the threads table and if it isn't, add it
        existing_thread_query = sqlalchemy.select([Threads]).\
            where(Threads.thread_number == thread_dict["thread_number"])
        existing_thread_rows = session.execute(existing_thread_query)
        existing_thread_row = existing_thread_rows.fetchone()
        if thread_row is None:
            # Create the thread row
            new_threads_row_dict = {}
            new_threads_row_dict["thread_number"] = thread_dict["thread_number"]
            new_threads_row = posts(**new_threads_row_dict)
            session.add(new_threads_row)
            session.flush()
            thread_id = new_threads_row.thread_id
        else:
            # Grab ID from existing row
            thread_id = existing_thread_row.thread_id



        # Update the thread row
        if thread_dict["thread_is_sticky"]:
            #TODO
            pass
        if thread_dict["thread_is_locked"]:
            #TODO
            pass
        #TODO

        # Find what posts we have from this thread we have in the DB
        existing_posts_query = sqlalchemy.select([Posts]).\
            where(Posts.thread_id == thread_id)
        existing_posts_rows = session.execute(existing_posts_query)\



        for post_dict in thread_dict["posts"]:
            # Check if post is in DB
            pass#TODO






        # Grab all the posts for the thread in the DB for comparison
        # Compare each post in the thread
        # for each post, insert images
    except err:
        session.rollback()# Prevent DB damage
        logging.exception(err)
        raise# Propogate the exception so we can't ignore it

# /Posts

# Threads
def mark_thread_dead(session,board_config,thread_number):
    """Mark a thread in the DB as deleted"""
    thread_query = sqlalchemy.select([Threads]).\
        where(Threads.thread_number == thread_dict["thread_number"])
    thread_rows = session.execute(thread_query)
    thread_row = thread_rows.fetchone()
# /Threads


def debug():
    """Temp code for debug"""
    session = connect_to_db()

    return



def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","sql_functions_log.txt"))
        debug()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
