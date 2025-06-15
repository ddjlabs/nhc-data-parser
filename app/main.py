'''
===============================================================================
 National Hurricane Center WeeWX API
 Module: MAIN 
 Purpose: This is the main bootstrap to start the National Hurricane Center Data processing
 for my Tropical API. This program creates the following threads below to process the data:

     1. run_nhc_pipeline() : This function starts the NHC Pipeline to pull the raw data and DQ/sanitize it for consumption
     2. run_raw_file_cleanup() : This function clears the raw rss files that I pull after they are stale.
 
pip libraries we need to install: Please refer to the requirements.txt file that is located in the project folder.
================================================================================
'''
import os, logging, configobj, threading, time, signal
from datetime import timedelta
from configobj import ConfigObj
from common import common_utils
import nhc_data_puller

#Constants
CURR_DIR = os.getcwd()

C_CONFIG_FILE =os.path.realpath(os.path.join(CURR_DIR,"config","app.conf"))

#FOR DEBUGGING PURPOSES
#C_CONFIG_FILE =os.path.realpath(os.path.join(CURR_DIR,"app","config","app.conf"))

i_wait_time_seconds = 900 # Default to 15 minutes



#Main program functions (hooks for threads to call)
def run_nhc_pipeline():
    nhc_data_puller.get_rss_data(s_testmode_flag, i_check_interval_minute, s_raw_file_loc)

def run_cleanup():
    logger.info('Running Cleanup.')
    logger.info('Clean up Completed.')




#Classes/Functions for thread management
class ProgramKilled(Exception):
    pass
   
def signal_handler(signum, frame):
    raise ProgramKilled
    
class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs
        
    def stop(self):
                self.stopped.set()
                self.join()
    def run(self):
            while not self.stopped.wait(self.interval.total_seconds()):
                self.execute(*self.args, **self.kwargs)




# ===== START MAIN PROGRAM =====
try:
    if __name__ == "__main__":
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        #Clear the Screen
        common_utils.clear_screen()

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
        common_utils.clear_screen()
        logger.info('=========================================================')
        logger.info('National Hurricane Center WeeWx API')
        logger.info('Validating configuration file app.conf')


        logger.info('retrieving configuration values')
        if (common_utils.check_config_file(C_CONFIG_FILE) == True):
            config = ConfigObj(C_CONFIG_FILE)

        #Check Interval (minutes)
        i_check_interval_minute = config['DATAPULLER']['check_interval_min']
        i_wait_time_seconds = int(i_check_interval_minute) * 60
        logger.info(f'Interval Check set to {i_check_interval_minute} minutes')

        #Raw Files Location (for RSS Files)
        s_raw_file_loc = os.path.join(CURR_DIR,config['DATAPULLER']['raw_files_location'])
        logger.info(f'Raw RSS Files stored at: {s_raw_file_loc}')

        #Check test mode
        s_testmode_flag = config['TESTMODE']['enable_testing']
        if (s_testmode_flag == 'Y'):
            logger.info('TESTMODE Enabled')
        else:
            logger.info('TESTMODE Disabled')

        # Start the database
        logger.info('Configuring Database Connection')
        s_db_type = config['DB']['DBType']
        s_db_file = os.path.join(CURR_DIR,"app","data",config['DB']['database_filepath'])
        s_mariadb_conn = config['DB']['mariadb_connection_string']
        common_utils.start_db(s_db_type, s_db_file, s_mariadb_conn, s_testmode_flag)
        logger.info('Database Connection Ready')

        #Check for Test Mode for Executing the Pipeline only once. 
        #Else, Run the pipeline continuously breaking at the i_wait_time_seconds intervals

        if (s_testmode_flag == "Y"):
            #Start the NHC Pipeline
            logger.info('')
            logger.info('Starting NHC Pipeline Process [TEST-MODE] One Pass Only')

            #Run the Pipeline once at initial startup
            
            run_nhc_pipeline()
            
            logger.info("Starting Cleanup")
            run_cleanup
                    
            logger.info('Program Stopped.')
            logger.info('=========================================================')
            logger.info('')
            logger.info('')
        else:
            #Start the NHC Pipeline
            logger.info('')
            logger.info('Starting NHC Pipeline Process')

            #Run the Pipeline once at initial startup
            run_nhc_pipeline()
            
            #Assign the Jobs to a thread and start them.
            job_pipeline = Job(interval=timedelta(seconds=i_wait_time_seconds), execute=run_nhc_pipeline)
            job_pipeline.start()
        
            #Loop to monitor for signal terminates/kills
            while True:
                try:
                    time.sleep(1)
                except ProgramKilled:
                    logger.info("Program Aborted. stopping threads")
                    job_pipeline.stop()

                    logger.info("Starting Cleanup")
                    run_cleanup
                    
                    logger.info('Program Stopped.')
                    logger.info('=========================================================')
                    logger.info('')
                    logger.info('')
                    break

except Exception as gen_err:
    logger.error(gen_err)
    os.abort()

# ===== END MAIN PROGRAM =====