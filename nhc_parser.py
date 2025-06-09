import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
import pytz
from typing import Dict, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# Namespace for NHC RSS feed
NHC_NAMESPACE = {"nhc": "https://www.nhc.noaa.gov"}

def parse_coordinates(coord_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse latitude and longitude from coordinate string."""
    logger.debug(f"Parsing coordinates from: {coord_str}")
    if not coord_str or "," not in coord_str:
        logger.warning(f"Invalid coordinate string format: {coord_str}")
        return None, None
    try:
        lat_str, lon_str = coord_str.split(",")
        lat = float(lat_str.strip().replace("°", ""))
        lon = float(lon_str.strip().replace("°", ""))
        logger.debug(f"Parsed coordinates - lat: {lat}, lon: {lon}")
        return lat, lon
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing coordinates '{coord_str}': {str(e)}", exc_info=True)
        return None, None

def clean_numeric(value: str) -> int:
    """Extract numeric value from string, removing any non-numeric characters."""
    logger.debug(f"Cleaning numeric value: {value}")
    if not value:
        logger.debug("Empty value, returning 0")
        return 0
    try:
        numbers = re.sub(r'[^0-9]', '', value)
        result = int(numbers) if numbers else 0
        logger.debug(f"Cleaned numeric value: {result}")
        return result
    except Exception as e:
        logger.error(f"Error cleaning numeric value '{value}': {str(e)}", exc_info=True)
        return 0

def parse_datetime(dt_str: str) -> datetime:
    """Parse NHC datetime string to UTC datetime."""
    logger.debug(f"Parsing datetime from: {dt_str}")
    try:
        # Example format: "1100 AM EDT Sat Jun 10"
        dt = date_parser.parse(dt_str, fuzzy=True)
        logger.debug(f"Initial parsed datetime: {dt}")
        
        # If the year is not in the string, it will default to 1900
        if dt.year == 1900:
            current_year = datetime.utcnow().year
            dt = dt.replace(year=current_year)
            logger.debug(f"Updated year to current year: {dt}")
        
        # Convert to UTC
        dt = dt.astimezone(pytz.UTC)
        result = dt.replace(tzinfo=None)  # Remove timezone for SQLite
        logger.debug(f"Final UTC datetime: {result}")
        return result
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing datetime '{dt_str}': {str(e)}", exc_info=True)
        logger.warning(f"Returning current UTC time due to parse error")
        return datetime.utcnow()

def get_storm_data(item) -> Optional[Dict]:
    """Extract storm data from RSS item."""
    logger.debug("Extracting storm data from RSS item")
    
    # Try to find the Cyclone element with namespace
    cyclone = item.find("nhc:Cyclone", NHC_NAMESPACE)
    
    # If not found with namespace, try without namespace
    if not cyclone:
        logger.debug("No nhc:Cyclone element found, trying without namespace")
        cyclone = item.find("Cyclone")
    
    if not cyclone:
        logger.debug("No Cyclone element found in RSS item")
        return None
        
    logger.debug(f"Found Cyclone element: {cyclone.name}")
    
    # Extract basic storm information - try with namespace first, then without
    def get_element_text(parent, tag_name):
        # Try with namespace first
        element = parent.find(f"nhc:{tag_name}", NHC_NAMESPACE)
        if not element:
            # Try without namespace
            element = parent.find(tag_name)
        return getattr(element, "text", "").strip() if element else ""
    
    storm_data = {
        "storm_id": get_element_text(cyclone, "atcf"),
        "storm_name": get_element_text(cyclone, "name"),
        "storm_type": get_element_text(cyclone, "type"),  # Changed from 'Type' to 'type'
        "wallet": get_element_text(cyclone, "wallet"),
        "movement": get_element_text(cyclone, "movement"),
        "headline": get_element_text(cyclone, "headline"),
    }
    
    logger.debug(f"Extracted storm data: {storm_data}")
    
    # Parse coordinates
    center = get_element_text(cyclone, "center")
    lat, lon = parse_coordinates(center)
    storm_data["latitude"] = lat
    storm_data["longitude"] = lon
    
    # Parse numeric values
    pressure = get_element_text(cyclone, "pressure")
    wind = get_element_text(cyclone, "wind")
    storm_data["pressure"] = clean_numeric(pressure)
    storm_data["wind_speed"] = clean_numeric(wind)
    
    # Parse datetime
    dt_str = get_element_text(cyclone, "datetime")
    storm_data["report_date"] = parse_datetime(dt_str)
    
    # Get additional data from item
    storm_data["report"] = getattr(item.find("description"), "text", "").strip()
    storm_data["report_link"] = getattr(item.find("link"), "text", "").strip()
    
    # Generate wallet URL
    if storm_data["wallet"]:
        storm_data["wallet_url"] = f"https://www.nhc.noaa.gov/nhc_{storm_data['wallet'].lower()}.xml"
    
    return storm_data

def fetch_rss_feed(url: str) -> Optional[BeautifulSoup]:
    """Fetch and parse RSS feed."""
    logger.info(f"Fetching RSS feed from: {url}")
    try:
        logger.debug("Sending HTTP GET request...")
        response = requests.get(url, timeout=10)
        logger.debug(f"Received response with status code: {response.status_code}")
        response.raise_for_status()
        
        # Log a sample of the response to help with debugging
        logger.debug(f"Response content sample (first 200 chars): {response.text[:200]}")
        
        logger.debug("Parsing XML content...")
        soup = BeautifulSoup(response.text, 'xml')
        logger.debug("Successfully parsed XML content")
        
        # Check for namespaces in the document
        root = soup.find('rss')
        if root and root.attrs:
            namespaces = {k.split(':')[1]: v for k, v in root.attrs.items() if k.startswith('xmlns:')}
            logger.debug(f"Found XML namespaces: {namespaces}")
            
        return soup
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching RSS feed: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error parsing RSS feed: {str(e)}", exc_info=True)
        return None
