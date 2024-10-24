import praw
import os
import json
import codecs

# Reddit API Anmeldeinformationen
reddit = praw.Reddit(client_id='u9wPL-7SY7LwVNTrImjS-w',
                     client_secret='3Y-1RHbp2rizAZRRji79OdIdImQx5w',
                     user_agent='FinBot/0.1 by FinBot_BA')

# Liste der Finanz-Subreddits
subreddits = ['wallstreetbets']

# Sammeln von Beiträgen
posts = []

try:
    for subreddit in subreddits:
        subreddit_obj = reddit.subreddit(subreddit)
        for submission in subreddit_obj.top(limit=1):
            # Sammeln der Top 10 Kommentare mit Text
            submission.comments.replace_more(limit=0)  # Entfernen von MoreComments Objekten
            top_comments = [comment for comment in submission.comments.list() if isinstance(comment.body, str) and comment.body.lower() not in ['[removed]', '[deleted]']][:10]
            comments_data = [
                {
                    "body": comment.body,
                    "score": comment.score
                } for comment in top_comments
            ]

            # Hinzufügen der gesammelten Daten zum Post
            posts.append({
                "title": submission.title,
                "selftext": submission.selftext,
                "created_utc": submission.created_utc,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "id": submission.id,
                "permalink": submission.permalink,
                "subreddit": subreddit,
                "is_self": submission.is_self,
                "link_flair_text": submission.link_flair_text,
                "top_comments": comments_data
            })
except Exception as e:
    print(f"Fehler beim Abrufen der Beiträge: {e}")

# Speichern der Daten als JSON-Datei
if os.path.exists('reddit_finance_posts.json'):
    print("Die Datei reddit_finance_posts.json existiert bereits und wird überschrieben.")

with codecs.open('reddit_finance_posts.json', 'w', encoding='utf-8') as json_file:
    json.dump(posts, json_file, ensure_ascii=True, indent=4)

print("Die Reddit-Beiträge wurden erfolgreich gespeichert.")
