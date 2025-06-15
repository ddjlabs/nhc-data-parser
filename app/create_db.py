import os, logging, configobj, time, signal
from configobj import ConfigObj
from common import common_utils, db_manager

#Constants
CURR_DIR = os.getcwd()

#IN DEBUG MODE
C_CONFIG_FILE =os.path.realpath(os.path.join(CURR_DIR,"config","app.conf"))
#FOR DEBUGGING PURPOSES
#C_CONFIG_FILE =os.path.realpath(os.path.join(CURR_DIR,"app","config","app.conf"))

# Gets or creates a logger
logger = logging.getLogger(__name__)  

# set log level
logger.setLevel(logging.INFO)

# define file handler and set formatter
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(funcName)s : %(message)s')
screen_handler = logging.StreamHandler()
screen_handler.setLevel(logging.INFO)
screen_handler.setFormatter(formatter)
logger.addHandler(screen_handler)

#Pull configuration items
try:
    common_utils.clear_screen()
    logger.info('=========================================================')
    logger.info('National Hurricane Center WeeWx API')
    logger.info('Create Database Script')
    logger.info('')

    #Get Configuration data from the configuration file
    logger.info('retrieving configuration values from app.conf')
    config = ConfigObj(C_CONFIG_FILE)

    #Check test mode
    s_testmode_flag = config['TESTMODE']['enable_testing']
    if (s_testmode_flag == 'Y'):
        logger.info('TESTMODE Enabled')
        
        #Get the sample file location
        s_rss_seed_file = os.path.realpath(os.path.join(CURR_DIR,"app","config",config['TESTMODE']['seed_sample_data']))
        logger.info(f'using RSS Seed File: {s_rss_seed_file}')

    else:
        logger.info('TESTMODE Disabled')

        #Get the rss seed file location
        s_rss_seed_file = os.path.realpath(os.path.join(CURR_DIR,"app","config",config['DB']['rss_feed_data']))
        logger.info(f'using RSS Seed File: {s_rss_seed_file}')


    # Create the database!
    s_db_type = config['DB']['DBType']
    s_db_file = os.path.join(CURR_DIR,"app","data",config['DB']['database_filepath'])
    s_mariadb_conn = config['DB']['mariadb_connection_string']

    #Build out the database connection
    if s_db_type == 'mariadb':
        db_manager.db_connection = s_mariadb_conn
    elif s_db_type == 'sqlite':
        db_manager.db_connection = 'sqlite:///' + s_db_file      
    else:
        raise Exception('DB Type ' + s_db_type + ' is not an allowed type. Update the app.conf with the correct value')

    db_manager.build_database()
    db_manager.load_rss_feed_data(s_rss_seed_file)
    

except Exception as err:
    logger.error(err)
    os.abort()