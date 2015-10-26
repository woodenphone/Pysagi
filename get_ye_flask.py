#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     26/10/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from utils import * # General utility functions
import board_config


from flask import Flask
app = Flask(__name__)


@app.route("/hello")
def hello():
    return "Hello World!"


@app.route("/info")
def info():
    dir_path = os.path.join("hosted", "futabilly")
    subdirs = os.walk(dir_path)[1]
    return "Hello World!"


@app.route("/<board_shortname>/threads.json")
def serve_catalog(board_shortname):
    file_path = os.path.join("hosted", "futabilly", board_shortname, "threads.json")
    with open(file_path, "r") as f:
        data = f.read()
    return data


@app.route("/<board_shortname>/res/<int:thread_num>.json")
def serve_thread(board_shortname,thread_num):
    file_path = os.path.join("hosted", "futabilly", board_shortname, "res", str(thread_num)+".json")
    with open(file_path, "r") as f:
        data = f.read()
    return data


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","get_ye_flask-log.txt"))
        app.debug = True
        app.run()
        logging.info("After app.run()")
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()


