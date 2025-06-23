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
from moviepy.editor import *
from datetime import datetime
import dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

dotenv.load_dotenv()
my_client_id = os.getenv("YOUR_CLIENT_ID")
my_client_secret = os.getenv("YOUR_CLIENT_SECRET")

class RedditVideoGenerator:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=my_client_id,
            client_secret=my_client_secret,
            user_agent="RedditVideoBot/1.0"
        )
        
        self.audio_dir = "audio"
        self.screenshots_dir = "screenshots"
        self.videos_dir = "videos"
        self.background_dir = "background_videos"
        
        for directory in [self.audio_dir, self.screenshots_dir, self.videos_dir, self.background_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.processed_posts_file = "processed_posts.json"
        self.processed_posts = self.load_processed_posts()
        
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.API_SERVICE_NAME = 'youtube'
        self.API_VERSION = 'v3'
        self.CLIENT_SECRETS_FILE = 'client_secret.json'
        self.youtube = None
    
    def load_processed_posts(self):
        try:
            with open(self.processed_posts_file, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def save_processed_posts(self):
        with open(self.processed_posts_file, 'w') as f:
            json.dump(list(self.processed_posts), f)
    
    def authenticate_youtube(self):
        credentials = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                credentials = pickle.load(token)
        
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CLIENT_SECRETS_FILE, self.SCOPES)
                credentials = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)
        
        self.youtube = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=credentials)
        return self.youtube
    
    def generate_video_metadata(self, post_data, comments_data):
        title = f"Reddit Story: {post_data['title'][:60]}..."
        if len(post_data['title']) <= 60:
            title = f"Reddit Story: {post_data['title']}"
        
        description = f"""🔥 Reddit Story from r/AskReddit 🔥

Original Post: {post_data['title']}

{post_data.get('text', '')[:500]}{'...' if len(post_data.get('text', '')) > 500 else ''}

📝 Featured Comments:
"""
        
        for i, comment in enumerate(comments_data[:3]):
            description += f"\n{i+1}. {comment['body'][:100]}{'...' if len(comment['body']) > 100 else ''}"
        
        description += f"""

🎯 Don't forget to LIKE and SUBSCRIBE for more Reddit stories!
💬 Share your thoughts in the comments below!

#Reddit #AskReddit #RedditStories #Stories #Entertainment
"""
        
        tags = [
            "reddit", "askreddit", "reddit stories", "stories", "entertainment",
            "reddit compilation", "reddit posts", "reddit comments", "viral",
            "funny", "interesting", "discussion", "community", "social media"
        ]
        
        return title, description, tags
    
    def upload_to_youtube(self, video_path, post_data, comments_data):
        print("Uploading video to YouTube...")
        
        if not self.youtube:
            self.authenticate_youtube()
        
        title, description, tags = self.generate_video_metadata(post_data, comments_data)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '24',
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')
        
        try:
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            error = None
            retry = 0
            
            while response is None:
                try:
                    print(f"Uploading file... Attempt {retry + 1}")
                    status, response = insert_request.next_chunk()
                    if status:
                        print(f"Upload progress: {int(status.progress() * 100)}%")
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        error = f"Server error: {e}"
                        retry += 1
                        if retry > 5:
                            print(f"Upload failed after 5 retries: {error}")
                            return None
                        time.sleep(2 ** retry)
                    else:
                        raise
                except Exception as e:
                    print(f"Upload error: {e}")
                    return None
            
            if response is not None:
                if 'id' in response:
                    video_id = response['id']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"✅ Video uploaded successfully!")
                    print(f"🔗 Video URL: {video_url}")
                    print(f"📺 Video ID: {video_id}")
                    
                    self.add_thumbnail_if_available(video_id)
                    
                    return {
                        'video_id': video_id,
                        'video_url': video_url,
                        'title': title
                    }
                else:
                    print(f"Upload failed: {response}")
                    return None
        
        except HttpError as e:
            print(f"HTTP Error during upload: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during upload: {e}")
            return None
    
    def add_thumbnail_if_available(self, video_id):
        thumbnail_path = os.path.join(self.screenshots_dir, "post_*.png")
        import glob
        thumbnails = glob.glob(thumbnail_path)
        
        if thumbnails:
            try:
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnails[0])
                ).execute()
                print("✅ Thumbnail uploaded successfully!")
            except Exception as e:
                print(f"Failed to upload thumbnail: {e}")
    
    def get_reddit_post(self, subreddit_name="AskReddit", limit=10):
        print(f"Fetching posts from r/{subreddit_name}...")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        
        for submission in subreddit.hot(limit=limit):
            if submission.id in self.processed_posts:
                continue
            
            if submission.over_18:
                continue
            
            if not submission.selftext and not submission.title:
                continue
            
            print(f"Selected post: {submission.title[:50]}...")
            return submission
        
        print("No suitable posts found!")
        return None
    
    def get_comments(self, submission, max_comments=5, max_words=100):
        print("Fetching comments...")
        
        submission.comments.replace_more(limit=0)
        
        selected_comments = []
        
        for comment in submission.comments:
            if not hasattr(comment, 'body') or comment.body in ['[deleted]', '[removed]']:
                continue
            
            if len(comment.body.split()) > max_words:
                continue
            
            if len(comment.body.split()) < 5:
                continue
            
            selected_comments.append({
                'id': comment.id,
                'body': comment.body,
                'score': comment.score
            })
            
            if len(selected_comments) >= max_comments:
                break
        
        selected_comments.sort(key=lambda x: x['score'], reverse=True)
        print(f"Selected {len(selected_comments)} comments")
        
        return selected_comments
    
    def text_to_speech(self, text, filename):
        print(f"Generating TTS for: {filename}")
        
        engine = pyttsx3.init()
        
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)
        
        filepath = os.path.join(self.audio_dir, f"{filename}.wav")
        engine.save_to_file(text, filepath)
        engine.runAndWait()
        
        return filepath
    
    def setup_browser(self):
        print("Setting up browser...")
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        
        driver = webdriver.Firefox(options=options)
        return driver
    
    def take_screenshot(self, driver, url, post_id, comment_ids=None):
        print(f"Taking screenshots for post: {post_id}")
        
        driver.get(url)
        time.sleep(3)
        
        screenshots = {}
        
        try:
            post_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='post-content']"))
            )
            
            post_filename = f"post_{post_id}.png"
            post_path = os.path.join(self.screenshots_dir, post_filename)
            post_element.screenshot(post_path)
            screenshots['post'] = post_path
            
            if comment_ids:
                for i, comment_id in enumerate(comment_ids):
                    try:
                        comment_selector = f"[data-testid='comment']"
                        comment_elements = driver.find_elements(By.CSS_SELECTOR, comment_selector)
                        
                        if i < len(comment_elements):
                            comment_filename = f"comment_{comment_id}.png"
                            comment_path = os.path.join(self.screenshots_dir, comment_filename)
                            comment_elements[i].screenshot(comment_path)
                            screenshots[f'comment_{i}'] = comment_path
                    
                    except Exception as e:
                        print(f"Error taking screenshot for comment {comment_id}: {e}")
        
        except Exception as e:
            print(f"Error taking screenshots: {e}")
        
        return screenshots
    
    def create_video(self, post_data, comments_data, screenshots, audio_files):
        print("Creating video...")
        
        clips = []
        
        if 'post' in screenshots and 'post' in audio_files:
            post_audio = AudioFileClip(audio_files['post'])
            post_img = ImageClip(screenshots['post']).set_duration(post_audio.duration)
            post_clip = post_img.set_audio(post_audio)
            clips.append(post_clip)
        
        for i, comment in enumerate(comments_data):
            comment_key = f'comment_{i}'
            if comment_key in screenshots and comment_key in audio_files:
                comment_audio = AudioFileClip(audio_files[comment_key])
                comment_img = ImageClip(screenshots[comment_key]).set_duration(comment_audio.duration)
                comment_clip = comment_img.set_audio(comment_audio)
                clips.append(comment_clip)
        
        if not clips:
            print("No clips to process!")
            return None
        
        main_video = concatenate_videoclips(clips, method="compose")
        
        background_files = [f for f in os.listdir(self.background_dir) if f.endswith('.mp4')]
        
        if background_files:
            background_file = random.choice(background_files)
            background_path = os.path.join(self.background_dir, background_file)
            
            try:
                background = VideoFileClip(background_path)
                
                if background.duration < main_video.duration:
                    background = background.loop(duration=main_video.duration)
                else:
                    background = background.subclip(0, main_video.duration)
                
                main_video_resized = main_video.resize(height=background.h//2).set_position(('center', 'center'))
                
                final_video = CompositeVideoClip([background, main_video_resized])
                
            except Exception as e:
                print(f"Error adding background: {e}")
                final_video = main_video
        else:
            final_video = main_video
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"reddit_video_{post_data['id']}_{timestamp}.mp4"
        output_path = os.path.join(self.videos_dir, output_filename)
        
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
        
        for clip in clips:
            clip.close()
        if 'final_video' in locals():
            final_video.close()
        
        print(f"Video saved: {output_path}")
        return output_path
    
    def generate_and_upload_video(self, subreddit="AskReddit"):
        print("Starting video generation...")
        
        submission = self.get_reddit_post(subreddit)
        if not submission:
            return None
        
        comments = self.get_comments(submission)
        if not comments:
            print("No suitable comments found!")
            return None
        
        audio_files = {}
        
        post_text = f"{submission.title}. {submission.selftext}" if submission.selftext else submission.title
        audio_files['post'] = self.text_to_speech(post_text, f"post_{submission.id}")
        
        for i, comment in enumerate(comments):
            audio_files[f'comment_{i}'] = self.text_to_speech(
                comment['body'], 
                f"comment_{comment['id']}"
            )
        
        driver = self.setup_browser()
        try:
            comment_ids = [comment['id'] for comment in comments]
            screenshots = self.take_screenshot(
                driver, 
                f"https://reddit.com{submission.permalink}", 
                submission.id,
                comment_ids
            )
        finally:
            driver.quit()
        
        post_data = {
            'id': submission.id,
            'title': submission.title,
            'text': submission.selftext,
            'url': submission.permalink
        }
        
        video_path = self.create_video(post_data, comments, screenshots, audio_files)
        
        if not video_path:
            print("Failed to create video!")
            return None
        
        result = {
            'video_path': video_path,
            'post_data': post_data,
            'comments_data': comments
        }
        
        print(f"✅ Video generation complete: {video_path}")
        
        while True:
            upload_choice = input("\nDo you want to upload this video to YouTube? (y/n): ").lower().strip()
            if upload_choice in ['y', 'yes']:
                youtube_result = self.upload_to_youtube(video_path, post_data, comments)
                if youtube_result:
                    result.update(youtube_result)
                else:
                    print("Failed to upload to YouTube, but video was created successfully.")
                break
            elif upload_choice in ['n', 'no']:
                print("Video saved locally. Skipping YouTube upload.")
                break
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        
        self.processed_posts.add(submission.id)
        self.save_processed_posts()
        
        print(f"✅ Process complete!")
        return result

if __name__ == "__main__":
    generator = RedditVideoGenerator()
    
    result = generator.generate_and_upload_video("AskReddit")
    
    if result:
        print(f"Success! Video saved at: {result['video_path']}")
        if 'video_url' in result:
            print(f"YouTube URL: {result['video_url']}")
    else:
        print("Failed to generate video")