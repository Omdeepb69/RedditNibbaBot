import praw
import pyttsx3
import os
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from moviepy.editor import *
from datetime import datetime
import dotenv

# Enhanced environment loading
dotenv.load_dotenv()
my_client_id = os.getenv("REDDIT_CLIENT_ID") or os.getenv("YOUR_CLIENT_ID")
my_client_secret = os.getenv("REDDIT_CLIENT_SECRET") or os.getenv("YOUR_CLIENT_SECRET")

class RedditVideoGenerator:
    def __init__(self):
        """Initialize with ultimate error handling"""
        # Verify credentials exist
        if not my_client_id or not my_client_secret:
            raise ValueError("""
❌ Missing Reddit API credentials. Please:
1. Create a .env file
2. Add your credentials:
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
""")
        
        print("\n🔍 Verifying Reddit API credentials...")
        print(f"Client ID: {my_client_id[:3]}...{my_client_id[-3:]}")
        print(f"Client Secret: {my_client_secret[:3]}...{my_client_secret[-3:]}")
        
        try:
            # Initialize with timeout and retry
            self.reddit = praw.Reddit(
                client_id=my_client_id.strip(),
                client_secret=my_client_secret.strip(),
                user_agent="desktop:RedditVideoBot:v3.0 (by /u/beast-fx2556)",
                timeout=10,
                retry_on_error=True
            )
            
            # Test with simple API call
            try:
                test = self.reddit.subreddit('all').hot(limit=1)
                next(test)  # Force API call
                print("✅ Reddit API connection successful")
            except Exception as api_error:
                print(f"""
❌ API test failed: {api_error}
                
🔧 Troubleshooting Guide:
1. DOUBLE-CHECK your credentials at https://www.reddit.com/prefs/apps
2. Ensure your app is 'script' type (not 'web app')
3. Verify your Reddit account email is confirmed
4. Check for typos in .env file
5. Wait 10 minutes if you recently changed credentials
6. Try generating NEW credentials
""")
                raise

        except Exception as e:
            print(f"❌ Reddit API initialization failed: {str(e)}")
            raise

        # Rest of initialization
        self.setup_directories()
        self.processed_posts = self.load_processed_posts()

    def setup_directories(self):
        """Create required directories"""
        dirs = ["audio", "screenshots", "videos", "background_videos"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            print(f"📁 Created directory: {d}")

    def load_processed_posts(self):
        """Load processed posts safely"""
        try:
            if os.path.exists("processed_posts.json"):
                with open("processed_posts.json", 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            print(f"⚠️ Error loading processed posts: {e}")
            return set()

    # [Rest of your methods remain unchanged]

def main():
    """Entry point with ultimate error handling"""
    print("="*50)
    print("Reddit Video Generator v3.0".center(50))
    print("="*50)
    
    try:
        generator = RedditVideoGenerator()
        print("\n🚀 Ready to generate videos!")
        
    except Exception as e:
        print(f"\n💥 Startup failed: {str(e)}")
        print("\n🔧 Final Checks:")
        print("1. Your .env file should be in the same folder")
        print("2. File must contain EXACTLY:")
        print("REDDIT_CLIENT_ID=your_id_here")
        print("REDDIT_CLIENT_SECRET=your_secret_here")
        print("3. No quotes or extra spaces around credentials")

if __name__ == "__main__":
    main()