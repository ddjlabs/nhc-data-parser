'''
===============================================================================
 National Hurricane Center WeeWX API
 Module: Data Puller
 Purpose: This library
 
 pip libraries we need to install: sqlalchemy, pytz, requests, bs4, configobj, lxml
================================================================================
'''
import os, logging, configobj, bs4, requests
from configobj import ConfigObj
from bs4 import BeautifulSoup
from common import common_utils, db_manager
from common.db_manager import rssData, storms

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


def get_rss_data(s_testmode_flag, s_interval_min, s_raw_file_loc):
    try:
        # Set all counters
        i_feed_cnt = 0
        i_updated_feed_cnt = 0
        i_skipped_feed_cnt = 0
        i_storms_cnt = 0
        i_skipped_storms_cnt = 0

        logger.info('=====')
        logger.info('Getting RSS Data from nhc.noaa.gov')

        # Pull the active feeds from the Database
        o_nhc_feed_list = db_manager.get_active_feed_list()

        #Iterate through the data and pull and parse the RSS data from the National Hurricane Center and post it into the database.
        for o_feed in o_nhc_feed_list:

            i_file_update_cnt = 0

            logger.info(f'Processing Feed: {o_feed.feed_name} | RSS url: {o_feed.feed_url}')
            
            # fetch the rss feed via requests and using BeautifulSoup
            rss_source = requests.get(o_feed.feed_url)
            soup = BeautifulSoup(rss_source.content, 'xml')

            '''
            print(f'title : {soup.title.text}')
            print(f'Publish Date: {soup.pubDate.text}')
            print(f'Version: {soup.rss.get("version")}')
            print(f'language: {getattr(soup.language, "text", "")}')
            print(f'Description: {getattr(soup.description, "text", "")}')
            '''
            #Build Filename for this feed to file in the raw data folder
            s_file_timestamp = str(common_utils.convert_nhc_datetime(soup.pubDate.text).strftime("%Y%m%d_%H%M%S"))
            s_file_name = os.path.join(s_raw_file_loc,(o_feed.feed_name).replace(' ','-') + "_" + s_file_timestamp + ".xml")

            #Get all item elements from the RSS Feed file
            item_list = soup.findAll("item")

            for i in item_list:
                #Create a rss Data record
                wx_dates = []    
                r = rssData()

                # Map the item data to the RssData Object       
                r.feed_name = o_feed.feed_name
                r.item_title = i.title.text                

                # Convert the Publish Date data to a python Datetime object for UTC timezone
                r.item_pubdate = common_utils.convert_nhc_datetime(i.pubDate.text)

                #See if the item already exists in the database
                b_exists = db_manager.check_existing_rss_data(o_feed.feed_name, r.item_title, r.item_pubdate)

                if b_exists is False:
                    #Since the check returned false, we do not have this record in our database. Therefore, we need to add the record

                    r.item_link = i.link.text
                    r.item_guid = i.guid.text
                    # print(f'Author: {i.author.text}')
                                        
                    #Parse out the datetime object to fill in the year, period, and day in the raw database table
                    wx_dates = common_utils.parse_wx_date(r.item_pubdate)
                    r.wx_year = wx_dates["year"]
                    r.wx_period = wx_dates["period"]
                    r.wx_day = wx_dates["day"]

                    # Convert the html-based description to text.
                    soup_item_desc = BeautifulSoup(i.description.text,"html.parser")

                    r.item_description = soup_item_desc.text
                    #r.item_description = i.description.text  #Preserving the HTML

                    #Post the Record
                    i_new_id = db_manager.add_rss_data(r)
                                        
                    # Get Cyclone Data (if exists)
                    cyclone_data = i.findAll("nhc:Cyclone")

                    for c in cyclone_data:
                        o_storm = storms()
                        wx_coordinates = []
                        
                        s_storm_name = c.find("nhc:name")
                        o_storm.storm_name = s_storm_name.text
                        o_storm.report_dt = r.item_pubdate
                        
                        # see if we have the record already
                        b_exists = db_manager.check_existing_storm_data(o_storm.storm_name, o_storm.report_dt) 
            
                        if b_exists is False:
                            
                            o_storm.storm_type = c.type.text
                        
                            # Get the center of the storm coordinates from the data
                            wx_coordinates = common_utils.parse_center_coordinates(c.center.text)
                            o_storm.storm_center_lat = wx_coordinates["lat"]
                            o_storm.storm_center_long = wx_coordinates["long"]

                            o_storm.storm_wallet = c.wallet.text
                            o_storm.atcf = c.atcf.text
                
                            o_storm.storm_movement = c.movement.text
                            o_storm.storm_pressure = c.pressure.text
                            o_storm.storm_winds = c.wind.text
                            o_storm.storm_headline = c.headline.text
                            o_storm.rss_data_id = i_new_id
                    
                            # Add the record
                            db_manager.add_storm_data((o_storm))
                            o_storm = None

                            # Increment the storm record counter
                            i_storms_cnt += 1
                        else:
                            # Increment the Skipped storm record counter
                            i_skipped_storms_cnt += 1

                    # Increment the updated feed counter
                    i_updated_feed_cnt += 1
                    i_file_update_cnt += 1
                else:
                    # Increment the skipped record counter
                    i_skipped_feed_cnt += 1

                r = None            
            
            # Increment the Feed counter
            i_feed_cnt += 1

            #Write the data to the raw-data directory if we loaded it to the database
            if i_file_update_cnt > 0:
                f_rss_source = open(s_file_name,'w')                
                f_rss_source.write(rss_source.text)
                f_rss_source.close()
            

        logger.info(f'Feeds Processed: {i_feed_cnt} | Items Updated: {i_updated_feed_cnt} | Items Skipped: {i_skipped_feed_cnt} | Storms updated: {i_storms_cnt} | Storms Skipped: {i_skipped_storms_cnt}')
        
        #Report back the wait interval (in minutes) as long as we are not in test mode.
        if s_testmode_flag == 'N':
            logger.info(f'Waiting {s_interval_min} minutes until the next check....')

    except Exception as err:
        logger.error(err)