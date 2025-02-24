import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from openai import OpenAI

load_dotenv()

# Initialize apps
slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET"))
flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)
youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Add route for Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # Handle URL verification challenge
    if request.json.get("type") == "url_verification":
        return jsonify({"challenge": request.json["challenge"]})
    # Handle all other events
    return handler.handle(request)

@slack_app.message("knock knock")
def ask_who(message, say):
    say("_Who's there?_")

@slack_app.event("app_mention")
def handle_mention(event, say):
    user_query = event["text"].split(">")[1].strip()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate specific YouTube search queries"},
            {"role": "user", "content": f"Educational videos about: {user_query}"}
        ],
        max_tokens=50
    )
    refined_query = response.choices[0].message.content.strip()
    search_response = youtube.search().list(
        q=refined_query,
        type="video",
        part="id,snippet",
        maxResults=3
    ).execute()

    response_text = f"Here are some educational videos about '{user_query}':\n\n"
    for item in search_response["items"]:
        video_title = item["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        response_text += f"• {video_title}\n{video_url}\n\n"
    say(response_text)

@slack_app.event("message")
def handle_message(body, logger):
    print(body)

if __name__ == "__main__":
    flask_app.run(port=3000)