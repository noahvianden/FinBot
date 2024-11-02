import os
import json
import logging
import praw
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, filename='reddit_fetcher.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Reddit API credentials (replace with your own)
reddit = praw.Reddit(client_id='u9wPL-7SY7LwVNTrImjS-w',
                         client_secret='3Y-1RHbp2rizAZRRji79OdIdImQx5w',
                         user_agent='FinBot/0.1 by FinBot_BA')


# Rate limiter to respect Reddit's API limits
class RateLimiter:
    def __init__(self, max_calls, period):
        self.lock = threading.Lock()
        self.calls = 0
        self.max_calls = max_calls
        self.period = period
        self.start_time = time.time()

    def wait(self):
        with self.lock:
            self.calls += 1
            elapsed = time.time() - self.start_time
            if elapsed >= self.period:
                self.calls = 0
                self.start_time = time.time()
            elif self.calls > self.max_calls:
                sleep_time = self.period - elapsed
                logging.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                self.calls = 0
                self.start_time = time.time()


rate_limiter = RateLimiter(max_calls=100, period=60)  # Adjust according to Reddit's API policy


# Function to get comment data recursively
def get_comment_tree(comment):
    if isinstance(comment, praw.models.Comment):
        comment_data = {
            'body': comment.body,
            'score': comment.score,
            'replies': [get_comment_tree(reply) for reply in comment.replies]
        }
        return comment_data
    else:
        return None


# Function to fetch a post and its comments
def get_post_with_comments(post_id):
    try:
        rate_limiter.wait()
        logging.info(f"Fetching post ID: {post_id}")
        submission = reddit.submission(id=post_id)

        # Fetch comments and maintain nested structure
        submission.comments.replace_more(limit=None)
        comments = [get_comment_tree(comment) for comment in submission.comments]

        post_data = {
            "title": submission.title,
            "selftext": submission.selftext,
            "id": submission.id,
            "created_utc": submission.created_utc,
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "comments": comments
        }
        return post_data
    except Exception as e:
        logging.error(f"Error fetching post ID {post_id}: {e}")
        return None


# Function to process a single file of posts
def process_file(input_file, output_file, processed_posts):
    logging.info(f"Processing file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            post = json.loads(line)
            post_id = post.get('id')
            if post_id in processed_posts:
                continue
            post_data = get_post_with_comments(post_id)
            if post_data:
                json.dump(post_data, outfile, ensure_ascii=False)
                outfile.write('\n')
                processed_posts.add(post_id)
            # Save progress after each post
            with open('processed_posts.txt', 'a', encoding='utf-8') as f:
                f.write(post_id + '\n')


# Main function to traverse directories and process posts
def process_posts(data_dir, start_point=None):
    """
    data_dir: Root directory where the posts are stored.
    start_point: Tuple (year, month, day, subreddit, filename) to resume processing.
    """
    processed_posts = set()
    # Load processed post IDs from file if exists
    if os.path.exists('processed_posts.txt'):
        with open('processed_posts.txt', 'r', encoding='utf-8') as f:
            processed_posts = set(line.strip() for line in f)

    start_year, start_month, start_day, start_subreddit, start_filename = start_point if start_point else (
    None, None, None, None, None)
    start_processing = not start_point  # Start immediately if no start point
    for year in sorted(os.listdir(data_dir)):
        if not os.path.isdir(os.path.join(data_dir, year)):
            continue
        if start_year and year < start_year:
            continue
        year_dir = os.path.join(data_dir, year)
        for month in sorted(os.listdir(year_dir)):
            if not os.path.isdir(os.path.join(year_dir, month)):
                continue
            if start_month and year == start_year and month < start_month:
                continue
            month_dir = os.path.join(year_dir, month)
            for filename in sorted(os.listdir(month_dir)):
                if not filename.endswith('.jsonl'):
                    continue
                day = filename.split('_')[3]  # Extract day from filename
                subreddit = filename.split('_')[1]
                if start_day and year == start_year and month == start_month and day < start_day:
                    continue
                if start_subreddit and year == start_year and month == start_month and day == start_day and subreddit < start_subreddit:
                    continue
                if start_filename and year == start_year and month == start_month and day == start_day and subreddit == start_subreddit and filename < start_filename:
                    continue
                start_processing = True
                if not start_processing:
                    continue
                input_file = os.path.join(month_dir, filename)
                output_dir = os.path.join('output', year, month)
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, filename)
                if os.path.exists(output_file):
                    logging.info(f"Output file already exists, skipping: {output_file}")
                    continue
                process_file(input_file, output_file, processed_posts)


# Example usage
if __name__ == "__main__":
    data_directory = './historical_post_data_clean'  # Replace with your data directory path
    # To resume from a specific point, set start_point to (year, month, day, subreddit, filename)
    start_point = None  # e.g., ('2021', '08', '15', 'python', 'reddit_python_2021_08_15.jsonl')
    process_posts(data_directory, start_point)
