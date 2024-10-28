import praw
import os
import json
import codecs
import logging
from helper.helper import important_subreddits

####################################
# ---------- Konfiguration ----------
####################################

# Reddit API Anmeldeinformationen
reddit = praw.Reddit(client_id='u9wPL-7SY7LwVNTrImjS-w',
                         client_secret='3Y-1RHbp2rizAZRRji79OdIdImQx5w',
                         user_agent='FinBot/0.1 by FinBot_BA')

# Logging-Konfiguration
logging.basicConfig(filename='log/reddit_data_collection.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

####################################
# ---------- Methoden --------------
####################################

# Funktion zum Abrufen von Kommentaren und Antworten
def get_comment_data(comment, depth=1):
    global api_token_count
    api_token_count += 1  # Zähle jeden API-Aufruf
    comment_data = {
        "body": comment.body,  # Kommentartext
        "score": comment.score,  # Bewertung des Kommentars
        "replies": [get_comment_data(reply, depth + 1) for reply in comment.replies if
                    isinstance(reply, praw.models.Comment)]  # Rekursive Abfrage der Antworten
    }
    return comment_data

# Funktion zum Abrufen von Beiträgen innerhalb eines festen Zeitrahmens
def get_posts_in_timeframe(subreddit, max_submissions, max_comments_layer_1):
    global api_token_count
    posts = []
    try:
        logging.info(f"Methode: get_posts_in_timeframe wurde aufgerufen")
        logging.info(f"Subreddit: {subreddit}")
        subreddit_obj = reddit.subreddit(subreddit)
        # Suche nach Beiträgen innerhalb des angegebenen Zeitrahmens
        for submission in subreddit_obj.new(limit=max_submissions):
            api_token_count += 1  # Zähle jeden API-Aufruf

            # Sammeln der Top-Kommentare
            submission.comments.replace_more(limit=0)  # Entfernen von MoreComments Objekten, um alle Kommentare zu laden
            top_comments = [
                get_comment_data(comment)
                for comment in submission.comments.list()
                if isinstance(comment.body, str) and comment.body.lower() not in ['[removed]', '[deleted]']
            ][:max_comments_layer_1]  # Beschränkung auf die maximale Anzahl der Kommentare

            # Hinzufügen der gesammelten Daten zum Post
            posts.append({
                "subreddit": subreddit,  # Name des Subreddits
                "title": submission.title,  # Titel des Beitrags
                "selftext": submission.selftext,  # Text des Beitrags
                "id": submission.id,  # ID des Beitrags
                "permalink": submission.permalink,  # Permalink zum Beitrag
                "created_utc": submission.created_utc,  # Erstellungszeit in UTC
                "score": submission.score,  # Bewertung des Beitrags
                "upvote_ratio": submission.upvote_ratio,  # Verhältnis der Upvotes
                "num_comments": submission.num_comments,  # Anzahl der Kommentare
                "top_comments": top_comments  # Gesammelte Top-Kommentare
            })
            logging.info(f"Anzahl der benötigten Tokens für Post '{submission.title}': {api_token_count}")
            api_token_count = 0  # Zähler zurücksetzen für den nächsten Post
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Beiträge: {e}")
    return posts, api_token_count

# Funktion zum Abrufen eines einzelnen Beitrags über die ID
def get_post_by_id(post_id, max_comments_layer_1):
    global api_token_count
    try:
        logging.info(f"Methode: get_post_by_id wurde aufgerufen")
        logging.info(f"Post ID: {post_id}")
        submission = reddit.submission(id=post_id)
        api_token_count += 1  # Zähle jeden API-Aufruf

        # Sammeln der Top-Kommentare
        submission.comments.replace_more(limit=0)  # Entfernen von MoreComments Objekten, um alle Kommentare zu laden
        top_comments = [
            get_comment_data(comment)
            for comment in submission.comments.list()
            if isinstance(comment.body, str) and comment.body.lower() not in ['[removed]', '[deleted]']
        ][:max_comments_layer_1]  # Beschränkung auf die maximale Anzahl der Kommentare

        # Hinzufügen der gesammelten Daten zum Post
        post_data = {
            "subreddit": submission.subreddit.display_name,  # Name des Subreddits
            "title": submission.title,  # Titel des Beitrags
            "selftext": submission.selftext,  # Text des Beitrags
            "id": submission.id,  # ID des Beitrags
            "permalink": submission.permalink,  # Permalink zum Beitrag
            "created_utc": submission.created_utc,  # Erstellungszeit in UTC
            "score": submission.score,  # Bewertung des Beitrags
            "upvote_ratio": submission.upvote_ratio,  # Verhältnis der Upvotes
            "num_comments": submission.num_comments,  # Anzahl der Kommentare
            "top_comments": top_comments  # Gesammelte Top-Kommentare
        }
        logging.info(f"Anzahl der benötigten Tokens für Post '{submission.title}': {api_token_count}")
        return post_data, api_token_count
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Beitrags mit ID {post_id}: {e}")
        return None

####################################
# ------------ Main ----------------
####################################

# Methode zum Abrufen eines Beitrags per ID und Hinzufügen zu den Posts
def fetch_and_add_post_by_id(post_id, max_comments_layer_1, all_posts, total_api_calls):
    logging.info(f"post_id: {post_id} wurde aufgerufen")
    post_data, api_calls = get_post_by_id(post_id, max_comments_layer_1)
    if post_data:
        all_posts.append(post_data)
        total_api_calls += api_calls
    return total_api_calls

# Methode zum Abrufen von Beiträgen aus wichtigen Subreddits
def fetch_posts_from_subreddits(subreddits, max_submissions, max_comments_layer_1, all_posts, total_api_calls):
    for subreddit in subreddits:
        posts, api_calls = get_posts_in_timeframe(subreddit, max_submissions, max_comments_layer_1)
        all_posts.extend(posts)
        total_api_calls += api_calls
    return total_api_calls

# Main-Methode
def main():
    # Zähler für die API-Token-Anzahl
    global api_token_count
    api_token_count = 0
    max_submissions = 10  # Maximale Anzahl der Beiträge, die von einem Subreddit abgerufen werden sollen
    max_comments_layer_1 = 10  # Maximale Anzahl der ersten Schicht von Kommentaren, die abgerufen werden sollen

    logging.info(f"----------------------------------------------------------------------------------")
    logging.info(f"Main Methode gestartet")

    # Sammeln von Beiträgen innerhalb des Zeitrahmens
    all_posts = []
    total_api_calls = 0

    # Beispiel zum Abrufen eines Beitrags über die ID
    total_api_calls = fetch_and_add_post_by_id('10aywle', max_comments_layer_1, all_posts, total_api_calls)

    # Abrufen von Beiträgen aus den wichtigen Subreddits (auskommentiert)
    # total_api_calls = fetch_posts_from_subreddits(['stocks'], max_submissions, max_comments_layer_1, all_posts, total_api_calls)

    # Speichern der Daten als json-Datei
    if os.path.exists('json/reddit_finance_posts.json'):
        logging.warning("Die Datei reddit_finance_posts.json existiert bereits und wird überschrieben.")

    with codecs.open('json/reddit_finance_posts.json', 'w', encoding='utf-8') as json_file:
        json.dump(all_posts, json_file, ensure_ascii=True, indent=4)  # Speichern der gesammelten Beiträge in einer JSON-Datei

    logging.info("Die Reddit-Beiträge wurden erfolgreich gespeichert")
    logging.info(f"----------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
