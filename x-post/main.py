import requests
from bs4 import BeautifulSoup
import logging
import os
import json
from dotenv import load_dotenv
import tweepy
import google.generativeai as genai
from flask import Flask, request, jsonify
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Load environment variables
load_dotenv()
app = Flask(__name__)

class InstagramScraper:
    def __init__(self, post_url):
        self.post_url = post_url

    def fetch_post_details(self):
        try:
            response = requests.get(self.post_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', {'name': 'description'})
            if not meta_tag:
                logging.warning("Could not find the description meta tag.")
                return None

            description = meta_tag.get('content')
            if not description:
                logging.warning("Could not extract description from meta tag.")
                return None

            og_image_tag = soup.find('meta', {'property': 'og:image'})
            if not og_image_tag:
                logging.warning("Could not find the og:image meta tag.")
                return None

            image_url = og_image_tag.get('content')
            if not image_url:
                logging.warning("Could not extract image URL from og:image tag.")
                return None

            return {"caption": description, "image_url": image_url}

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error occurred: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def summarize_for_tweet(caption, max_length=280):
    """Summarizes a caption using Google's Gemini API for a tweet."""
    try:
        print("summarize_for_tweet called")
        print(f"Caption received: {caption}")
        genai.configure(api_key="AIzaSyAIoZdXR3eOu9FxUdGxqOLqc8_E7KRoygI")
        print("Gemini API configured")

        model = genai.GenerativeModel('models/gemini-1.5-pro')
        print("Gemini model loaded")

        prompt = f"Summarize this Instagram caption into a tweet (under {max_length} characters):\n{caption}"
        print(f"Prompt being sent to Gemini: {prompt}")

        response = model.generate_content(prompt)
        print(f"Gemini API response: {response}")
        tweet_summary = response.text.strip()

        if len(tweet_summary) > max_length:
            tweet_summary = tweet_summary[:max_length]

        print(f"Tweet summary: {tweet_summary}")
        return tweet_summary

    except Exception as e:
        print(f"Error during summarization: {e}")
        return None
def post_to_x(tweet_text):
    max_attempts = 3
    attempt = 1

    while attempt <= max_attempts:
        try:
            consumer_key = os.environ.get("X_CONSUMER_KEY")
            consumer_secret = os.environ.get("X_CONSUMER_SECRET")
            access_token = os.environ.get("X_ACCESS_TOKEN")
            access_token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET")

            if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
                raise ValueError("Missing one or more X credentials")

            print(f"Attempt {attempt}: Using credentials: consumer_key={consumer_key[:5]}..., access_token={access_token[:5]}...")
            
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            response = client.create_tweet(text=tweet_text)
            print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
            return True

        except requests.exceptions.ConnectTimeout:
            print(f"Attempt {attempt} failed: Connection to X timed out.")
            if attempt == max_attempts:
                print("Max attempts reached. Giving up.")
                return False
            time.sleep(5)  # Wait 5 seconds before retrying
            attempt += 1
        except tweepy.TweepyException as te:
            print(f"Tweepy error: {te}")
            return False
        except Exception as e:
            print(f"General error posting to X: {e}")
            return False
        
@app.route('/post-tweet', methods=['POST'])
def post_tweet_endpoint():
    """API endpoint to summarize a caption and post a tweet."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        caption = data.get('caption')
        if not caption:
            return jsonify({"error": "No caption provided"}), 400

        tweet_text = summarize_for_tweet(caption)
        if not tweet_text:
            return jsonify({"error": "Failed to summarize caption"}), 500

        if post_to_x(tweet_text):
            return jsonify({"message": "Tweet posted successfully!"}), 200
        else:
            return jsonify({"error": "Failed to post tweet"}), 500

    except Exception as e:
        logging.exception("Error in /post-tweet endpoint")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "Welcome to my Flask app!"

@app.route('/scrape-and-tweet', methods=['GET'])
def scrape_and_tweet_endpoint():
    print("scrape_and_tweet_endpoint was called!")
    try:
        post_url = "https://www.instagram.com/p/DG_V-Cit_Fp/?img_index=4&igsh=aTlleDhweTAwNTJo"
        print(f"post_url: {post_url}")
        scraper = InstagramScraper(post_url)
        result = scraper.fetch_post_details()
        print(f"result: {result}")

        if not result:
            return jsonify({"error": "Failed to fetch Instagram post details."}), 500

        caption = result['caption']
        print(f"caption: {caption}")

        tweet_text = summarize_for_tweet(caption)
        print(f"tweet_text: {tweet_text}")

        if not tweet_text:
            return jsonify({"error": "Failed to summarize caption"}), 500

        if post_to_x(tweet_text):
            return jsonify({"message": "Tweet posted successfully!"}), 200
        else:
            return jsonify({"error": "Failed to post tweet"}), 500

    except Exception as e:
        logging.exception("Error in /scrape-and-tweet endpoint")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)