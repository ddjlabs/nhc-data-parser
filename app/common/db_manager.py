import os, sys, datetime, logging
from datetime import datetime
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, and_, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql.expression import null
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.sqltypes import DateTime

# Gets or creates a logger
logger = logging.getLogger(__name__)  

# set log level
logger.setLevel(logging.INFO)

# define file handler and set formatter
screen_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(funcName)s : %(message)s')
screen_handler.setFormatter(formatter)
logger.addHandler(screen_handler)

#Database Connection String
db_connection = str('')

#RSS Seed Values File Location
s_rss_seed_file = str('')

Base = declarative_base()


# ===== DATA MODEL START ===== 
class rssData(Base):
    __tablename__ = "rss_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_name = Column(String(100), nullable=False)
    wx_year = Column(Integer, nullable=False)
    wx_period = Column(Integer, nullable=False)
    wx_day = Column(Integer, nullable=False)
    item_title = Column(String(2500), nullable=False)
    item_description = Column(String(4000), nullable=True)
    item_pubdate = Column(DateTime, nullable=False)
    item_link = Column(String(500), nullable=True)
    item_guid = Column(String(500), nullable=True)
    status = Column(Integer, nullable=False, default=0)
    created_date = Column(DateTime, default=datetime.utcnow)

class rss_data_images(Base):
    __tablename__ = "rss_data_images"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rssData_id = Column(Integer, nullable=False)
    image_name = Column(String(200), nullable=True)
    image_url = Column(String(300), nullable=False)

class nhc_feeds(Base):
    __tablename__ = "nhc_feeds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_name = Column(String(100), nullable=False)
    feed_category = Column(String(100), nullable=True)
    feed_url = Column(String(300), nullable=False)
    feed_file_name = Column(String(100), nullable=False)
    active_yn = Column(String(1), nullable=False, default='Y')
    created_date = Column(DateTime, default=datetime.utcnow)

    def __init__(self, feed_name, feed_category, feed_url, feed_file_name, active_yn):
        self.feed_name = feed_name
        self.feed_category = feed_category
        self.feed_url = feed_url
        self.feed_file_name = feed_file_name
        self.active_yn = active_yn
        self.created_date = datetime.utcnow()

class storms(Base):
    __tablename__ = "storms"
    storm_id = Column(Integer, primary_key=True, autoincrement=True)
    storm_name = Column(String(50), nullable=False)
    storm_type = Column(String(50), nullable=False)
    storm_wallet = Column(String(10), nullable=True)
    storm_center_lat = Column(Integer, nullable=True)
    storm_center_long = Column(Integer, nullable=True)
    report_dt = Column(DateTime, nullable=False)
    atcf = Column(String(100), nullable=True)
    storm_movement = Column(String(300), nullable=True)
    storm_pressure = Column(String(300), nullable=True)
    storm_winds = Column(String(300), nullable=True)
    storm_headline = Column(String(2000), nullable=True)
    rss_data_id = Column(Integer, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# ===== END DATA MODEL =====

# Functions
def build_database():
    try:

        # Create an engine that stores data in the target directory
        engine = create_engine(db_connection)
        
        # Create all tables in the engine. This is equivalent to "Create Table"
        # statements in raw SQL.
        Base.metadata.create_all(engine)

    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        engine.dispose()

def load_rss_feed_data(s_rss_seed_file):
    try:
        #Now iterate through the seed file and display the results
        logger.info("Importing the RSS Source data into the Database")
        
        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb    
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()


        o_file = open(s_rss_seed_file, 'r',encoding='utf8')
    
        for s_line in o_file:
            #We are going to skip all lines that have a "#" in the first character
            if (s_line.find('#',0,1) == -1):
                arr_line = []
                arr_line = s_line.split(',')
            
                #Load the value  
                add_nhc_feed_data(nhc_feeds(feed_name=arr_line[0],feed_category=arr_line[1], feed_url=arr_line[2], feed_file_name=arr_line[3], active_yn=arr_line[4].strip()))
    
        o_file.close()
        logger.info('RSS Sources Loaded')

    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def add_nhc_feed_data(obj):
    try:
        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb
    
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()

        new_data = nhc_feeds(
            feed_name = obj.feed_name,
            feed_category = obj.feed_category,
            feed_url = obj.feed_url,
            feed_file_name = obj.feed_file_name,
            active_yn = obj.active_yn
        )
        session.add(new_data)
        session.commit()
        new_data = None
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def add_rss_data(obj):
    try:
        i_new_id = 0
        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb
    
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()

        new_data = rssData(
                            feed_name = obj.feed_name, 
                            wx_year = obj.wx_year, 
                            wx_period = obj.wx_period, 
                            wx_day = obj.wx_day,
                            item_title = obj.item_title,
                            item_description = obj.item_description, 
                            item_pubdate = obj.item_pubdate, 
                            item_link = obj.item_link, 
                            item_guid = obj.item_guid
                            )
        session.add(new_data)
        session.flush()

        #Get the new id from the added record
        session.refresh(new_data)
        i_new_id = new_data.id
        
        #Commit the record in the database
        session.commit()
        new_data = None
        return i_new_id
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def add_rss_data_image(obj):
    try:
        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb
    
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()
    
        # Insert a RSS Image record
        new_data =  rss_data_images(
                            rssData_id = obj.rssData_id, 
                            image_name = obj.image_name, 
                            image_url = obj.image_url
                            )
        session.add(new_data)
        session.commit()
        new_data = None
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def add_storm_data(obj):
    try:
        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb    
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()
    
        # Insert a Storm record in the Storms table
        new_data = storms(
                            storm_name = obj.storm_name,
                            storm_type = obj.storm_type,
                            storm_wallet = obj.storm_wallet,
                            storm_center_lat = obj.storm_center_lat,
                            storm_center_long = obj.storm_center_long,
                            report_dt = obj.report_dt,
                            atcf = obj.atcf,
                            storm_movement = obj.storm_movement,
                            storm_pressure = obj.storm_pressure,
                            storm_winds = obj.storm_winds,
                            storm_headline = obj.storm_headline,
                            rss_data_id = obj.rss_data_id
                        )
        session.add(new_data)
        session.flush()

        session.commit()
        new_data = None
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def check_existing_rss_data(s_rss_feed_name, s_item_title, d_pubdate):
    try:
        i_rec_count = 0

        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb        
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()
        
        # Query the SQLite Database to see if you already have a record for the feed name, item Title, and Publish Date.
        # Return back the number of records and evaluate it.
        i_rec_count = session.query(rssData.id).filter(and_(rssData.feed_name == s_rss_feed_name, rssData.item_title == s_item_title, func.DATE(rssData.item_pubdate)==func.DATE(d_pubdate))).count()
       
        #If records are return, exit by sending TRUE (meaning exists), else exit sending FALSE (Does not exist)
        if i_rec_count > 0:
            return True
        else:
             return False
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def check_existing_storm_data(s_storm_name, d_reportdate):
    try:
        i_rec_count = 0

        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb        
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()
        
        # Query the SQLite Database to see if you already have a record for the Storm Name, PubDate
        # Return back the number of records and evaluate it.
        i_rec_count = session.query(storms.storm_id).filter(and_(storms.storm_name == s_storm_name, func.DATE(storms.report_dt)==func.DATE(d_reportdate))).count()

        #If records are return, exit by sending TRUE (meaning exists), else exit sending FALSE
        if i_rec_count > 0:
            return True
        else:
            return False
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()

def get_active_feed_list():
    try:
        sqldb = create_engine(db_connection)
        Base.metadata.bind = sqldb        
        DBSession = sessionmaker(bind=sqldb)
        session = DBSession()
        
        #Query all NHC Feeds that are active from the NHC_Feeds Table
        o_data = session.query(nhc_feeds).filter(nhc_feeds.active_yn == 'Y').all()
            
        return o_data
    except Exception as err:
        logger.error(err)
        raise (err)
    finally:
        session.close()
        sqldb.dispose()
  