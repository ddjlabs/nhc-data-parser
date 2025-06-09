import os
import json
import html2text
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

class RSSFeedToMarkdown:
    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        self.h2md = html2text.HTML2Text()
        self.h2md.ignore_links = False
        self.h2md.body_width = 0
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def fetch_rss_feed(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def parse_rss(self, xml_data):
        root = ET.fromstring(xml_data)
        channel = root.find('channel')
        items = []
        for item in channel.findall('item'):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            description = item.find('description').text
            items.append({
                'title': title,
                'link': link,
                'pub_date': pub_date,
                'description': description
            })
        return items

    def rss_to_markdown(self, items, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# NOAA NHC RSS Feed\n\n")
            f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for item in items:
                f.write(f"## [{item['title']}]({item['link']})\n")
                f.write(f"**Published:** {item['pub_date']}\n\n")
                # Convert HTML in description to Markdown, replacing <br> tags with newlines (case-insensitive)
                description_html = item['description'] if item['description'] else ''
                # Replace <br>, <br/>, <br /> in all case variations with \n
                import re
                description_html = re.sub(r'<br\s*/?>', '\n', description_html, flags=re.IGNORECASE)
                description_md = self.h2md.handle(description_html)
                # Remove any remaining <br> tags just in case
                description_md = re.sub(r'<br\s*/?>', '\n', description_md, flags=re.IGNORECASE)
                f.write(f"{description_md}\n\n")
                f.write("---\n\n")

    def process_feed(self, url, output_filename):
        xml_data = self.fetch_rss_feed(url)
        items = self.parse_rss(xml_data)
        output_path = os.path.join(self.output_dir, output_filename)
        self.rss_to_markdown(items, output_path)

    def process_from_json(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            feeds = json.load(f)
        for feed in feeds:
            url = feed['url']
            output_filename = feed.get('output', 'feed.md')
            self.process_feed(url, output_filename)

# Example usage:
# if __name__ == '__main__':
#     rss = RSSFeedToMarkdown(output_dir='output')
#     rss.process_from_json('feeds.json')
