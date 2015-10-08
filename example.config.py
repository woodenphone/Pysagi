#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     15/02/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os # for cross-platform paths


# File paths
root_path = os.path.join("F:\\tumblrsagi","download")

# mysql://scott:tiger@hostname/dbname
#sqlalchemy_login = "sqlite:///local.db"
sqlalchemy_login = "postgresql://postgres:postgres@localhost/example"
#sqlalchemy_login = "sqlite:///local.db"#TODO FIXME!
# Echo SQL crap from SQLAlchemy?
echo_sql = True


# Logging messages, see table below for possible options
console_log_level = 10
# these numbers are defined in the logging library
##CRITICAL = 50
##FATAL = CRITICAL
##ERROR = 40
##WARNING = 30
##WARN = WARNING
##INFO = 20
##DEBUG = 10
##NOTSET = 0




def main():
    pass

if __name__ == '__main__':
    main()
