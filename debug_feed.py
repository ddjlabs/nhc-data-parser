import requests
from bs4 import BeautifulSoup
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def debug_feed():
    url = "https://www.nhc.noaa.gov/index-ep.xml"
    logger.info(f"Fetching RSS feed from: {url}")
    
    try:
        # Fetch the feed
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.info(f"Received response with status code: {response.status_code}")
        
        # Print the first 500 characters to see the structure
        print("\n=== START OF FEED (first 500 chars) ===")
        print(response.text[:500])
        print("=== END OF FEED SAMPLE ===\n")
        
        # Find all namespace declarations in the XML
        namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', response.text)
        print("=== NAMESPACES FOUND ===")
        for prefix, uri in namespaces:
            print(f"Prefix: {prefix}, URI: {uri}")
        print("=== END NAMESPACES ===\n")
        
        # Parse the XML
        soup = BeautifulSoup(response.text, 'xml')
        if not soup:
            logger.error("Failed to parse XML")
            return
            
        # Try to find items
        items = soup.find_all('item')
        logger.info(f"Found {len(items)} items in feed")
        
        # Look for any Cyclone tags with different namespace prefixes
        print("\n=== SEARCHING FOR CYCLONE TAGS ===")
        cyclone_tags = []
        
        # Try with no namespace
        cyclones = soup.find_all('Cyclone')
        if cyclones:
            print(f"Found {len(cyclones)} Cyclone tags with no namespace")
            cyclone_tags.extend(cyclones)
            
        # Try with different namespaces
        for prefix, _ in namespaces:
            tag_name = f"{prefix}:Cyclone"
            cyclones = soup.find_all(tag_name)
            if cyclones:
                print(f"Found {len(cyclones)} {tag_name} tags")
                cyclone_tags.extend(cyclones)
                
        # Check each item for any tag containing "cyclone" (case insensitive)
        print("\n=== EXAMINING ITEMS FOR CYCLONE-RELATED TAGS ===")
        for i, item in enumerate(items[:5]):  # Check first 5 items
            print(f"\nItem {i+1}:")
            print(f"Title: {item.title.text if item.title else 'No title'}")
            
            # Print all direct children tags of the item
            print("Tags in this item:")
            for child in item.children:
                if hasattr(child, 'name') and child.name:
                    print(f"- {child.name}")
            
            # Look for any tag containing "cyclone" (case insensitive)
            cyclone_related = []
            for tag in item.find_all():
                if tag.name and 'cyclone' in tag.name.lower():
                    cyclone_related.append(tag)
            
            if cyclone_related:
                print(f"Found {len(cyclone_related)} cyclone-related tags:")
                for tag in cyclone_related:
                    print(f"- {tag.name}: {tag.text[:50]}...")
            else:
                print("No cyclone-related tags found in this item")
                
        # Print the full XML of the first item as a sample
        if items:
            print("\n=== SAMPLE ITEM XML ===")
            print(items[0].prettify())
            print("=== END SAMPLE ITEM XML ===")
            
    except Exception as e:
        logger.error(f"Error debugging feed: {e}", exc_info=True)

if __name__ == "__main__":
    debug_feed()
