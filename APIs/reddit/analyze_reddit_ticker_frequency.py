import os
import json
from collections import defaultdict, Counter
import datetime

start_time = datetime.datetime.now()

# Root directory containing all processed .jsonl files
data_dir = 'historical_data_clean/'

# Initialize nested dictionaries for counts
ticker_data_by_year = defaultdict(lambda: defaultdict(Counter))  # {year: {subreddit: Counter()}}
indicator_data_by_year = defaultdict(lambda: defaultdict(Counter))  # {year: {subreddit: Counter()}}

# Overall counts with subreddits and years
overall_ticker_counter = defaultdict(Counter)  # {ticker: Counter(subreddit: count)}
overall_indicator_counter = defaultdict(Counter)  # {indicator: Counter(subreddit: count)}
ticker_yearly_counter = defaultdict(Counter)  # {ticker: Counter(year: count)}
indicator_yearly_counter = defaultdict(Counter)  # {indicator: Counter(year: count)}

# Function to process each .jsonl file and update counters
def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            entry = json.loads(line.strip())

            # Extract relevant data
            subreddit = entry.get("subreddit")
            created = entry.get("created")
            matched_tickers = entry.get("matched", {}).get("tickers", [])
            matched_indicators = entry.get("matched", {}).get("market_indicators", [])

            # Determine the year from the UTC timestamp (updated method)
            year = datetime.datetime.fromtimestamp(created, datetime.timezone.utc).year

            # Update counts for tickers and indicators by year and subreddit
            for ticker in matched_tickers:
                ticker_data_by_year[year][subreddit][ticker] += 1
                overall_ticker_counter[ticker][subreddit] += 1  # Overall count by subreddit
                ticker_yearly_counter[ticker][year] += 1  # Yearly count

            for indicator in matched_indicators:
                indicator_data_by_year[year][subreddit][indicator] += 1
                overall_indicator_counter[indicator][subreddit] += 1  # Overall count by subreddit
                indicator_yearly_counter[indicator][year] += 1  # Yearly count

# Walk through all files in the data directory and its subdirectories
for root, _, files in os.walk(data_dir):
    for file in files:
        if file.endswith('.jsonl'):
            file_path = os.path.join(root, file)
            process_file(file_path)

# Output file path
output_file_path = '../../old/analysis_output_finance_subreddits_after_parameter_tuning.txt'
# Output file path für Vergleiche
# output_file_path = '../../old/analysis_output_comparison_subreddits.txt'

# Write results to file
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    # # Write Ticker Frequencies by Year and Subreddit
    # output_file.write("Ticker Frequencies by Year and Subreddit:\n")
    # for year, subreddit_data in ticker_data_by_year.items():
    #     output_file.write(f"\nYear: {year}\n")
    #     for subreddit, counter in subreddit_data.items():
    #         output_file.write(f"  Subreddit: {subreddit}\n")
    #         for ticker, count in counter.most_common():
    #             output_file.write(f"    {ticker}: {count}\n")
    #
    # # Write Market Indicator Frequencies by Year and Subreddit
    # output_file.write("\nMarket Indicator Frequencies by Year and Subreddit:\n")
    # for year, subreddit_data in indicator_data_by_year.items():
    #     output_file.write(f"\nYear: {year}\n")
    #     for subreddit, counter in subreddit_data.items():
    #         output_file.write(f"  Subreddit: {subreddit}\n")
    #         for indicator, count in counter.most_common():
    #             output_file.write(f"    {indicator}: {count}\n")

    # Write Overall Ticker Frequencies with Subreddits (sorted by total count)
    output_file.write("\nOverall Ticker Frequencies with Subreddits:\n")
    for ticker, subreddit_counter in sorted(overall_ticker_counter.items(), key=lambda item: sum(item[1].values()),
                                            reverse=True):
        total_count = sum(subreddit_counter.values())
        output_file.write(f"{ticker}: {total_count}\n")
        for subreddit, count in subreddit_counter.items():
            output_file.write(f"  {subreddit}: {count}\n")

    # Write Overall Market Indicator Frequencies with Subreddits (sorted by total count)
    output_file.write("\nOverall Market Indicator Frequencies with Subreddits:\n")
    for indicator, subreddit_counter in sorted(overall_indicator_counter.items(),
                                               key=lambda item: sum(item[1].values()), reverse=True):
        total_count = sum(subreddit_counter.values())
        output_file.write(f"{indicator}: {total_count}\n")
        for subreddit, count in subreddit_counter.items():
            output_file.write(f"  {subreddit}: {count}\n")

    # # Write Yearly Ticker Frequencies
    # output_file.write("\nYearly Ticker Frequencies:\n")
    # for ticker, year_counter in ticker_yearly_counter.items():
    #     total_count = sum(year_counter.values())
    #     output_file.write(f"{ticker}: {total_count}\n")
    #     for year, count in year_counter.items():
    #         output_file.write(f"  Year {year}: {count}\n")
    #
    # # Write Yearly Market Indicator Frequencies
    # output_file.write("\nYearly Market Indicator Frequencies:\n")
    # for indicator, year_counter in indicator_yearly_counter.items():
    #     total_count = sum(year_counter.values())
    #     output_file.write(f"{indicator}: {total_count}\n")
    #     for year, count in year_counter.items():
    #         output_file.write(f"  Year {year}: {count}\n")

print(f"Analysis complete. Results saved to {output_file_path}")

end_time = datetime.datetime.now()
duration = end_time - start_time
print(f"Zeitdauer: {duration}")