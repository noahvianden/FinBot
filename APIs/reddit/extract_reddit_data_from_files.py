import json
import os
import re
from datetime import datetime, timezone
from helper.helper import companies_dict, market_indicators  # Import the Dictionary and the List from helper.py

# Input and output directories
input_dir = 'historical_data_raw/'  # Directory containing all .jsonl files
output_dir = 'historical_data_clean/'  # Directory for cleaned data

# Helper function to create the filename
def generate_filename(subreddit, created_utc):
    date = datetime.fromtimestamp(created_utc, timezone.utc)
    year = date.strftime('%Y')
    month = date.strftime('%m')

    # Create folders for year and month
    sub_dir = os.path.join(output_dir, year, month)
    return os.path.join(sub_dir, f"reddit_{subreddit}_{date.strftime('%Y_%m_%d')}.jsonl")

# Function to process and write the files
def process_reddit_data(file_path):
    # Combine company names and tickers into one list
    company_terms = [company.lower() for company in companies_dict.keys()] + [ticker.lower() for ticker in companies_dict.values()]
    # Build a combined regex pattern for companies
    company_pattern = re.compile(r'\b(' + '|'.join(re.escape(term) for term in company_terms) + r')\b')

    # Build a combined regex pattern for market indicators
    indicator_terms = [indicator.lower() for indicator in market_indicators]
    indicator_pattern = re.compile(r'\b(' + '|'.join(re.escape(term) for term in indicator_terms) + r')\b')

    # Open file handles dict
    file_handles = {}

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            entry = json.loads(line.strip())

            # Extract entry information
            subreddit = entry.get("subreddit")
            title = entry.get("title", "")
            selftext = entry.get("selftext", "")
            post_id = entry.get("id")
            created_utc = entry.get("created_utc")
            num_comments = entry.get("num_comments")

            # Skip entries without title and text
            if not title and not selftext:
                continue

            # Convert title and text to lowercase for search
            title_lower = title.lower()
            selftext_lower = selftext.lower()
            combined_text = title_lower + ' ' + selftext_lower

            # Find all matches in the text
            matched_tickers = set(company_pattern.findall(combined_text))
            matched_indicators = set(indicator_pattern.findall(combined_text))

            # If no matches found, skip
            if not matched_tickers and not matched_indicators:
                continue

            # Relevant data structure
            post_data = {
                "subreddit": subreddit,
                "title": title,
                "id": post_id,
                "created": created_utc,
                "num_comments": num_comments,
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

# Main function to process all .jsonl files in the directory
if __name__ == "__main__":
    start_time = datetime.now()

    # Process each .jsonl file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            file_path = os.path.join(input_dir, filename)
            print(f"Processing file: {filename}")
            process_reddit_data(file_path)

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Zeitdauer: {duration}")