#-------------------------------------------------------------------------------
# Name:        tables
# Purpose:  define the database for SQLAlchemy
#
# Author:      User
#
# Created:     08/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy# Database library
from sqlalchemy.ext.declarative import declarative_base# Magic for ORM
import sqlalchemy.dialects.postgresql # postgreSQL ORM (JSON, JSONB)

from utils import * # General utility functions



##class Example(Base):
##     """Class that defines the media table in the DB"""
##     __tablename__ = "example"
##     # Columns
##     # Locally generated
##     primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Only used as a primary key
##     date_added = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the media was saved
##     media_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# Should have a constant length since it's a hash
##     sha512base64_hash = sqlalchemy.Column(sqlalchemy.String(88))
##     sha512base64_hash = sqlalchemy.Column(sqlalchemy.dialects.postgresql.CHAR(88))
##     local_filename = sqlalchemy.Column(sqlalchemy.String(250))# Filename on local storage, file path is deterministically generated from this
##     remote_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())# Filename from original location (If any)
##     file_extention = sqlalchemy.Column(sqlalchemy.String(25))# ex. png, jpeg
##     extractor_used = sqlalchemy.Column(sqlalchemy.String(250))# internal name of the extractor used (function name of extractor)
##     # Video and Audio use these
##     yt_dl_info_json = sqlalchemy.Column(sqlalchemy.UnicodeText())
##     video_id = sqlalchemy.Column(sqlalchemy.UnicodeText())# The ID of the video used by the originating site
##     audio_id = sqlalchemy.Column(sqlalchemy.UnicodeText())# The ID of the audio used by the originating site
##     annotations = sqlalchemy.Column(sqlalchemy.UnicodeText())

# SQLAlchemy table setup
Base = declarative_base()

class Boards(Base):
    """Class that defines the boards table in the DB"""
    __tablename__ = "boards"
    # Columns
    board_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Local primary key
    board_shortname = sqlalchemy.Column(sqlalchemy.UnicodeText())# MUST be unique
    board_name = sqlalchemy.Column(sqlalchemy.UnicodeText())
    board_shortname = sqlalchemy.Column(sqlalchemy.UnicodeText())
    api_url = sqlalchemy.Column(sqlalchemy.UnicodeText())
    hidden = sqlalchemy.Column(sqlalchemy.Boolean())# Should this be hidden from users?



class Threads(Base):
    """Class that defines the threads table in the DB"""
    __tablename__ = "threads"
    # Columns
    thread_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Local primary key
    board_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("boards.board_id"))# Foreign key#TODO
    hidden = sqlalchemy.Column(sqlalchemy.Boolean())# Should this be hidden from users?
    #
    sticky = sqlalchemy.Column(sqlalchemy.Boolean())# was this thread a sticky?
    locked = sqlalchemy.Column(sqlalchemy.Boolean())# was this thread locked?
    #
    thread_number = sqlalchemy.Column(sqlalchemy.BigInteger)# Number of the thread on the origin server
    time_of_deletion = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time deletion was noticed
    time_last_updated = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time we last updated this thread
    time_las_bumped = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time last bump was noticed


    number_of_replies = None#TODO


class Posts(Base):
    """Class that defines the posts table in the DB"""
    __tablename__ = "posts"
    # Columns
    post_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Local primary key
    thread_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("threads.thread_id"))# Foreign key#TODO
    hidden = sqlalchemy.Column(sqlalchemy.Boolean())# Should this be hidden from users?
    #
    time_of_deletion = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time post deletion was noticed
    #
    post_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    post_text = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    poster_name = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    poster_tripcode = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    poster_email = sqlalchemy.Column(sqlalchemy.UnicodeText())#




class media(Base):
    """Class that defines the media table in the DB"""
    __tablename__ = "media"
    # Columns
    media_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Local primary key
    hidden = sqlalchemy.Column(sqlalchemy.Boolean())# Should this be hidden from users?
    banned = False# unknown use
    #
    poster_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())#Filename reported for origin
    board_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())# Filename on remote server
    local_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())# Filename in local storage
    #
    width = sqlalchemy.Column(sqlalchemy.BigInteger)# Width of full image
    height = sqlalchemy.Column(sqlalchemy.BigInteger)# Height of full image
    #
    filesize_in_bytes = sqlalchemy.Column(sqlalchemy.BigInteger)#
    md5_base64_hash = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    sha512base16_hash = sqlalchemy.Column(sqlalchemy.UnicodeText())#


class thumbnails(Base):
    """Class that defines the thumbnails table in the DB"""
    __tablename__ = "thumbnails"
    # Columns
    #
    thumbnail_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Local primary key
    hidden = sqlalchemy.Column(sqlalchemy.Boolean())# Should this be hidden from users?
    is_op_thumbnail = sqlalchemy.Column(sqlalchemy.Boolean())# TRUE: is op; FALSE: is reply
    #
    thumbnail_width = sqlalchemy.Column(sqlalchemy.BigInteger)# Width of thumbnail
    thumbnail_height = sqlalchemy.Column(sqlalchemy.BigInteger)# Height of thumbnail
    #
    local_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    filesize_in_bytes = sqlalchemy.Column(sqlalchemy.BigInteger)#
    md5_base64_hash = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    sha512_hash = sqlalchemy.Column(sqlalchemy.UnicodeText())#


class media_associations(Base):
    """Class that defines the media-thumbnail-post association table in the DB"""
    __tablename__ = "media_associations"
    # Columns
    association_id = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("posts.post_id")) # Local post ID
    media_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("media.media_id")) # Local media ID
    op_thumbnail_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("thumbnails.thumbnail_id")) # Local thumbnail ID of OP thumbnail
    reply_thumbnail_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("thumbnails.thumbnail_id")) # Local thumbnail ID of reply thumbnail
    spoilered = sqlalchemy.Column(sqlalchemy.Boolean())# IS the image spoilered in the post?
# /SQLAlchemy table setup



def create_example_db_sqllite():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    engine = sqlalchemy.create_engine("sqlite:///pysagi.sqllite", echo=True)
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
    session.commit()

    logging.debug("Example DB created")
    return

def create_example_db_postgres():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    # postgresql://username:password@host/database_name
    engine = sqlalchemy.create_engine("postgresql://postgres:postgres@localhost/pysagi", echo=True)
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
    session.commit()

    logging.debug("Example DB created")
    return


def main():
    setup_logging(log_file_path=os.path.join("debug","tables-log.txt"))
    create_example_db_postgres()

if __name__ == '__main__':
    main()
