import googleapiclient.discovery
import googleapiclient.errors
import datetime
import json
from helper.helper import companies_dict


def get_video_titles_and_comments_for_companies(companies):
    # Set up the YouTube API client
    api_service_name = "youtube"
    api_version = "v3"
    api_key = "YOUR_API_KEY"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

    video_data = []

    # Calculate the date 10 days ago
    ten_days_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)).isoformat()

    for company_name, symbol in companies.items():
        try:
            # Search for videos specifically related to the company's stock
            request = youtube.search().list(
                part="snippet",
                q=f"{company_name} Stock Analysis OR {company_name} Stock News OR {company_name} Share Price",
                type="video",
                relevanceLanguage="de",
                publishedAfter=ten_days_ago,
                maxResults=5
            )
            response = request.execute()

            # Calculate API token count for search request
            api_token_count = 100  # Each search request costs 100 quota points

            # Collect video titles and video IDs from the response
            for item in response.get("items", []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                created_at = item['snippet']['publishedAt']
                permalink = f"https://www.youtube.com/watch?v={video_id}"

                # Collect top 100 comments for each video
                top_comments = []
                try:
                    comments_request = youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        maxResults=100,
                        textFormat="plainText"
                    )
                    comments_response = comments_request.execute()
                    for comment in comments_response.get("items", []):
                        comment_body = comment['snippet']['topLevelComment']['snippet']['textDisplay']
                        comment_score = comment['snippet']['topLevelComment']['snippet']['likeCount']
                        replies = []

                        # Collect replies to the top-level comment
                        if comment['snippet']['totalReplyCount'] > 0:
                            replies_request = youtube.comments().list(
                                part="snippet",
                                parentId=comment['id'],
                                maxResults=100,
                                textFormat="plainText"
                            )
                            replies_response = replies_request.execute()
                            for reply in replies_response.get("items", []):
                                reply_body = reply['snippet']['textDisplay']
                                reply_score = reply['snippet']['likeCount']
                                replies.append({
                                    "body": reply_body,
                                    "score": reply_score
                                })

                        top_comments.append({
                            "body": comment_body,
                            "score": comment_score,
                            "replies": replies
                        })
                    # Each comment request costs 1 quota point
                    api_token_count += 1
                except googleapiclient.errors.HttpError as e:
                    print(f"An error occurred while fetching comments for video {video_id}: {e}")

                video_data.append({
                    "title": title,
                    "created_utc": created_at,
                    "num_comments": len(top_comments),
                    "id": video_id,
                    "permalink": permalink,
                    "top_comments": top_comments,
                    "api_token_count": api_token_count
                })

        except googleapiclient.errors.HttpError as e:
            print(f"An error occurred for {company_name}: {e}")

    return video_data


if __name__ == "__main__":
    try:
        # companies_dict = ["Apple"] # zum testen
        video_data = get_video_titles_and_comments_for_companies(companies_dict)

        # Convert the video data to JSON and save it to a file
        video_data_json = json.dumps(video_data, indent=4, ensure_ascii=False)
        with open("json/youtube_finance_posts.json", "w", encoding="utf-8") as f:
            f.write(video_data_json)

    except ValueError as e:
        print(e)
