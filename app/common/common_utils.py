import os, logging, xml, datetime, pytz, configobj 
from os import system, name
from datetime import datetime
from common import db_manager


# Gets or creates a logger
logger = logging.getLogger(__name__)  

# set log level
logger.setLevel(logging.INFO)

# define file handler and set formatter
screen_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(funcName)s : %(message)s')
screen_handler.setFormatter(formatter)
logger.addHandler(screen_handler)

# define our clear function
def clear_screen():
  
    # for windows
    if name == 'nt':
        _ = system('cls')
  
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

def check_config_file(s_path):
    try:
        if os.path.isfile(s_path):
            return True
        else:
            raise Exception(f'Config file not found at {s_path}')
            return False
    except Exception as err:
        logger.error(err)
        raise (err)


def start_db(s_db_type, s_db_file, s_mariadb_conn, s_testmode_flag):
    try:
        if s_db_type == 'mariadb':
            db_manager.db_connection = s_mariadb_conn
        elif s_db_type == 'sqlite':
            if os.path.isfile(s_db_file):
                #Database Exists!
                db_manager.db_connection = 'sqlite:///' + s_db_file
            else:    
                raise Exception('Database file Not found. Run create_db.py to initialize the database first.')
        else:
            raise Exception('DB Type ' + s_db_type + ' is not an allowed type. Update the app.conf with the correct value')
    except Exception as err:
        logger.error(err)
        raise (err)


# Data Conversion Functions
def get_months(s_data):
    if s_data.upper() == 'JAN':
        return 1
    elif s_data.upper() == 'FEB':
        return 2
    elif s_data.upper() == 'MAR':
        return 3
    elif s_data.upper() == 'APR':
        return 4
    elif s_data.upper() == 'MAY':
        return 5
    elif s_data.upper() == 'JUN':
        return 6
    elif s_data.upper() == 'JUL':
        return 7
    elif s_data.upper() == 'AUG':
        return 8
    elif s_data.upper() == 'SEP':
        return 9
    elif s_data.upper() == 'OCT':
        return 10
    elif s_data.upper() == 'NOV':
        return 11
    elif s_data.upper() == 'DEC':
        return 12
    else:
        return 'N/A'

def convert_nhc_datetime(s_data):
    #Sample string from NHC
    #Wed, 02 Jun 2021 11:17:33 GMT

    #Initialize the local timezone to GMT and the target timezone to UTC
    local_tz = pytz.timezone('GMT')
    target_tz = pytz.timezone('UTC')

    #Parse out the s_data string to get the integer values to create the datetime object
    i_day = int(s_data[5:7])
    i_month = get_months(s_data[8:11])
    i_year = int(s_data[12:16])
    i_hour = int(s_data[17:19])
    i_minute = int(s_data[20:22])
    i_second = int(s_data[23:25])

    #Now lets build a datatime object with the data fragments
    d_temp_dt = datetime(i_year,i_month,i_day,i_hour,i_minute,i_second)
    
    #Set the timezone to GMT for the temp datetime object. This is the default timezone published by NHC.
    d_temp_dt = local_tz.localize(d_temp_dt)

    #Convert to UTC for our database storage. we want all the datetime values set to a single timezone.
    d_final_dt = target_tz.normalize(d_temp_dt)

    #return the datetime object back to the calling application
    return d_final_dt


def parse_wx_date(d_input_dt):
    wx_dates = {
                "year": 1970,
                "period": 1,
                "day": 1
                }
    #Fill the Dictionary with the correct values from the imported datetime object.
    wx_dates["year"] = d_input_dt.strftime("%Y")
    wx_dates["period"] = d_input_dt.strftime("%m")
    wx_dates["day"] = d_input_dt.strftime("%d")

    #Send it back to the calling function
    return wx_dates

def parse_center_coordinates(s_center_data):
    wx_lat_long = {"lat": 0, "long":0}

    #Fill the Dictionary object with the correct values from the center value

    x = s_center_data.split(',')
    wx_lat_long["lat"] = x[0].strip(' ')
    wx_lat_long["long"] = x[1].strip(' ')

    return wx_lat_long
    