import praw
import re
from helper.helper import companies_dict, important_subreddits

# Reddit API Credentials
reddit = praw.Reddit(client_id='u9wPL-7SY7LwVNTrImjS-w',
                     client_secret='3Y-1RHbp2rizAZRRji79OdIdImQx5w',
                     user_agent='FinBot/0.1 by FinBot_BA')

# Function to filter posts mentioning companies
def filter_posts_by_company(posts, companies):
    filtered_posts = []
    for post in posts:
        for company_name, symbol in companies.items():
            if re.search(rf"\b({company_name}|{symbol})\b", post.title, re.IGNORECASE):
                filtered_posts.append(post.title)
                break
    return filtered_posts

# Loop through all important subreddits
all_filtered_posts = []
subreddit_match_counts = {}

for subreddit_name in important_subreddits:
    subreddit = reddit.subreddit(subreddit_name)
    posts = subreddit.new(limit=100)
    filtered_posts = filter_posts_by_company(posts, companies_dict)
    all_filtered_posts.extend(filtered_posts)
    subreddit_match_counts[subreddit_name] = len(filtered_posts)

# Display filtered posts
for idx, post in enumerate(all_filtered_posts, start=1):
    print(f"{idx}. {post}")

# Display match counts per subreddit
print("\nMatch counts per subreddit:")
for subreddit_name, count in subreddit_match_counts.items():
    print(f"{subreddit_name}: {count} matches")
