import json
import os
import re
from datetime import datetime, timezone
from helper.helper import companies_dict, market_indicators  # Import the Dictionary and the List from helper.py

# Input file and output directory
input_file = r'C:\Users\noahv\Downloads\r_stockmarket_posts.jsonl'
output_dir = 'historical_data_clean/'

# Helper function to create the filename
def generate_filename(subreddit, created_utc):
    date = datetime.fromtimestamp(created_utc, timezone.utc)
    year = date.strftime('%Y')
    month = date.strftime('%m')

    # Create folders for year and month
    sub_dir = os.path.join(output_dir, year, month)
    return os.path.join(sub_dir, f"reddit_{subreddit}_{date.strftime('%Y_%m_%d')}.jsonl")

# Function to process and write the files
def process_reddit_data():
    # Precompile regex patterns
    company_patterns = []
    for company, ticker in companies_dict.items():
        company_lower = company.lower()
        ticker_lower = ticker.lower()
        company_pattern = re.compile(r'\b' + re.escape(company_lower) + r'\b')
        ticker_pattern = re.compile(r'\b' + re.escape(ticker_lower) + r'\b')
        company_patterns.append((company, company_pattern))
        company_patterns.append((ticker, ticker_pattern))

    indicator_patterns = []
    for indicator in market_indicators:
        indicator_lower = indicator.lower()
        indicator_pattern = re.compile(r'\b' + re.escape(indicator_lower) + r'\b')
        indicator_patterns.append((indicator, indicator_pattern))

    # Open file handles dict
    file_handles = {}

    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            entry = json.loads(line.strip())

            # Extract entry information
            subreddit = entry.get("subreddit")
            title = entry.get("title", "")
            selftext = entry.get("selftext", "")
            post_id = entry.get("id")
            created_utc = entry.get("created_utc")

            # Skip entries without title and text
            if not title and not selftext:
                continue

            # Convert title and text to lowercase for search
            title_lower = title.lower()
            selftext_lower = selftext.lower()

            # Sets for found matches to avoid duplicates
            matched_tickers = set()
            matched_indicators = set()

            # Check for mention of companies and ticker symbols
            for name, pattern in company_patterns:
                if pattern.search(title_lower) or pattern.search(selftext_lower):
                    matched_tickers.add(name)

            # Check for mention of market indicators
            for indicator, pattern in indicator_patterns:
                if pattern.search(title_lower) or pattern.search(selftext_lower):
                    matched_indicators.add(indicator)

            # If no matches found, skip
            if not matched_tickers and not matched_indicators:
                continue

            # Relevant data structure
            post_data = {
                "subreddit": subreddit,
                "title": title,
                "id": post_id,
                "matched": {
                    "tickers": list(matched_tickers),
                    "market_indicators": list(matched_indicators)
                }
            }

            # Determine file for the post
            filename = generate_filename(subreddit, created_utc)

            # Write post_data to the file
            if filename not in file_handles:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                file_handles[filename] = open(filename, 'a', encoding='utf-8')

            file_handles[filename].write(json.dumps(post_data, ensure_ascii=False) + '\n')

    # Close all open file handles
    for f in file_handles.values():
        f.close()

if __name__ == "__main__":
    start_time = datetime.now()
    process_reddit_data()
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Zeitdauer: {duration}")
