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
import ponychan
import boards
import futabilly


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
    board_config = boards.get_settings(board_shortname)
    catalog_dict = ponychan.read_catalog(board_config)
    futabilly_catalog = futabilly.futabilly_format_catalog(board_config,catalog_dict)
    json_to_send = json.dumps(futabilly_catalog)
    return json_to_send


@app.route("/<board_shortname>/res/<int:thread_number>.json")
def serve_thread(board_shortname,thread_number):
    board_config = boards.get_settings(board_shortname)
    futabilly_thread_dict = ponychan.process_thread(board_config,thread_number)
    if futabilly_thread_dict is None:
        abort(404)
    json_to_send = json.dumps(futabilly_thread_dict)
    return json_to_send


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


