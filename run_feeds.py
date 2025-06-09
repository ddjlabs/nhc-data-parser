from rss_to_markdown import RSSFeedToMarkdown

if __name__ == '__main__':
    rss = RSSFeedToMarkdown(output_dir='output')
    rss.process_from_json('feeds.json')
