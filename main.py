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
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import glob
import logging

# Load environment variables
dotenv.load_dotenv()
my_client_id = os.getenv("YOUR_CLIENT_ID")
my_client_secret = os.getenv("YOUR_CLIENT_SECRET")

class RedditVideoGenerator:
    TOP_STORY_SUBREDDITS = [
        "AskReddit", "tifu", "relationships", "nosleep", "confession"
    ]

    def __init__(self, auto_upload=False):
        # Initialize Reddit API with better error handling
        if not my_client_id or not my_client_secret:
            raise ValueError("Reddit API credentials not found. Please check your .env file.")
        
        try:
            self.reddit = praw.Reddit(
                client_id=my_client_id.strip(),
                client_secret=my_client_secret.strip(),
                user_agent="script:RedditVideoBot:v1.0 (by /u/beast-fx2556)"
            )
            # Test the connection
            self.reddit.user.me()
            print("✅ Successfully authenticated with Reddit API")
        except Exception as e:
            print(f"❌ Failed to initialize Reddit API: {e}")
            print("Please verify your credentials in .env file and Reddit app settings")
            raise
        
        # Create directories
        self.audio_dir = "audio"
        self.screenshots_dir = "screenshots"
        self.videos_dir = "videos"
        self.background_dir = "background_videos"
        
        for directory in [self.audio_dir, self.screenshots_dir, self.videos_dir, self.background_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Load processed posts
        self.processed_posts_file = "processed_posts.json"
        self.processed_posts = self.load_processed_posts()
        
        # YouTube API settings
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.API_SERVICE_NAME = 'youtube'
        self.API_VERSION = 'v3'
        self.CLIENT_SECRETS_FILE = 'client_secret.json'
        self.youtube = None
        self.auto_upload = auto_upload
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    
    def load_processed_posts(self):
        """Load processed posts from JSON file, handling empty or corrupted files"""
        try:
            if os.path.exists(self.processed_posts_file):
                with open(self.processed_posts_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # Check if file is not empty
                        return set(json.loads(content))
                    else:
                        print("Warning: processed_posts.json is empty. Creating new set.")
                        return set()
            else:
                print("processed_posts.json not found. Creating new set.")
                return set()
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading processed posts: {e}. Creating new set.")
            return set()
    
    def save_processed_posts(self):
        """Save processed posts to JSON file"""
        try:
            with open(self.processed_posts_file, 'w') as f:
                json.dump(list(self.processed_posts), f, indent=2)
        except Exception as e:
            print(f"Error saving processed posts: {e}")
    
    def authenticate_youtube(self):
        """Authenticate with YouTube API"""
        credentials = None
        
        # Load existing credentials
        if os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    credentials = pickle.load(token)
            except Exception as e:
                print(f"Error loading credentials: {e}")
        
        # Refresh or get new credentials
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    credentials = None
            
            if not credentials:
                if not os.path.exists(self.CLIENT_SECRETS_FILE):
                    raise FileNotFoundError(f"YouTube client secrets file '{self.CLIENT_SECRETS_FILE}' not found.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CLIENT_SECRETS_FILE, self.SCOPES)
                credentials = flow.run_local_server(port=0)
            
            # Save credentials
            try:
                with open('token.pickle', 'wb') as token:
                    pickle.dump(credentials, token)
            except Exception as e:
                print(f"Error saving credentials: {e}")
        
        self.youtube = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=credentials)
        return self.youtube
    
    def generate_video_metadata(self, post_data, comments_data):
        """Generate YouTube video metadata"""
        subreddit = post_data.get('subreddit', 'AskReddit')
        title = f"Reddit Story from r/{subreddit}: {post_data['title'][:60]}..."
        if len(post_data['title']) <= 60:
            title = f"Reddit Story from r/{subreddit}: {post_data['title']}"
        
        # Create description
        description = f"""🔥 Reddit Story from r/{subreddit} 🔥

Original Post: {post_data['title']}

{post_data.get('text', '')[:500]}{'...' if len(post_data.get('text', '')) > 500 else ''}

📝 Featured Comments:
"""
        
        for i, comment in enumerate(comments_data[:3]):
            description += f"\n{i+1}. {comment['body'][:100]}{'...' if len(comment['body']) > 100 else ''}"
        
        description += f"""

🎯 Don't forget to LIKE and SUBSCRIBE for more Reddit stories!
💬 Share your thoughts in the comments below!

#Reddit #{subreddit} #RedditStories #Stories #Entertainment
"""
        
        tags = [
            "reddit", subreddit.lower(), "reddit stories", "stories", "entertainment",
            "reddit compilation", "reddit posts", "reddit comments", "viral",
            "funny", "interesting", "discussion", "community", "social media"
        ]
        
        return title, description, tags
    
    def upload_to_youtube(self, video_path, post_data, comments_data):
        """Upload video to YouTube"""
        print("Uploading video to YouTube...")
        
        if not self.youtube:
            try:
                self.authenticate_youtube()
            except Exception as e:
                print(f"YouTube authentication failed: {e}")
                return None
        
        title, description, tags = self.generate_video_metadata(post_data, comments_data)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '24',  # Entertainment
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        try:
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')
            
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
                        print(f"HTTP Error: {e}")
                        return None
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
        
        except Exception as e:
            print(f"Unexpected error during upload: {e}")
            return None
    
    def add_thumbnail_if_available(self, video_id):
        """Add thumbnail to YouTube video if available"""
        thumbnail_path = os.path.join(self.screenshots_dir, "post_*.png")
        thumbnails = glob.glob(thumbnail_path)
        
        if thumbnails and self.youtube:
            try:
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnails[0])
                ).execute()
                print("✅ Thumbnail uploaded successfully!")
            except Exception as e:
                print(f"Failed to upload thumbnail: {e}")
    
    def get_reddit_post(self, subreddit_name=None, limit=10):
        """Get a suitable Reddit post"""
        if subreddit_name is None:
            subreddit_name = random.choice(self.TOP_STORY_SUBREDDITS)
        print(f"Fetching posts from r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            for submission in subreddit.hot(limit=limit):
                if submission.id in self.processed_posts:
                    continue
                
                if submission.over_18:
                    continue
                
                if not submission.selftext and not submission.title:
                    continue
                
                # Skip posts that are too short
                if len(submission.title) < 10:
                    continue
                
                print(f"Selected post: {submission.title[:50]}...")
                submission.subreddit_name = subreddit_name
                return submission
            
            print("No suitable posts found!")
            return None
            
        except Exception as e:
            print(f"Error fetching Reddit posts: {e}")
            return None
    
    def get_comments(self, submission, max_comments=5, max_words=100):
        """Get suitable comments from a Reddit post"""
        print("Fetching comments...")
        
        try:
            submission.comments.replace_more(limit=0)
            
            selected_comments = []
            
            for comment in submission.comments:
                if not hasattr(comment, 'body') or comment.body in ['[deleted]', '[removed]']:
                    continue
                
                word_count = len(comment.body.split())
                if word_count > max_words or word_count < 5:
                    continue
                
                selected_comments.append({
                    'id': comment.id,
                    'body': comment.body,
                    'score': comment.score
                })
                
                if len(selected_comments) >= max_comments:
                    break
            
            # Sort by score (upvotes)
            selected_comments.sort(key=lambda x: x['score'], reverse=True)
            print(f"Selected {len(selected_comments)} comments")
            
            return selected_comments
            
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []
    
    def text_to_speech(self, text, filename):
        """Convert text to speech"""
        print(f"Generating TTS for: {filename}")
        
        try:
            engine = pyttsx3.init()
            
            # Configure TTS settings
            engine.setProperty('rate', 165)
            engine.setProperty('volume', 1.0)
            
            voices = engine.getProperty('voices')
            # Prefer female/en voices, else randomize
            preferred_voices = [v for v in voices if ('en' in v.languages[0] if hasattr(v, 'languages') and v.languages else 'en' in v.id) and ('female' in v.name.lower() or 'zira' in v.id.lower() or 'susan' in v.id.lower())]
            if not preferred_voices:
                preferred_voices = [v for v in voices if 'en' in (v.languages[0] if hasattr(v, 'languages') and v.languages else v.id)]
            if preferred_voices:
                chosen_voice = random.choice(preferred_voices)
                engine.setProperty('voice', chosen_voice.id)
            elif voices:
                engine.setProperty('voice', random.choice(voices).id)
            
            filepath = os.path.join(self.audio_dir, f"{filename}.wav")
            engine.save_to_file(text, filepath)
            engine.runAndWait()
            
            # Verify file was created
            if os.path.exists(filepath):
                return filepath
            else:
                print(f"Error: Audio file not created for {filename}")
                return None
                
        except Exception as e:
            print(f"Error generating TTS for {filename}: {e}")
            return None
    
    def setup_browser(self):
        """Setup Firefox browser with options"""
        print("Setting up browser...")
        
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            
            driver = webdriver.Firefox(options=options)
            return driver
            
        except Exception as e:
            print(f"Error setting up browser: {e}")
            raise
    
    def take_screenshot(self, driver, url, post_id, comment_ids=None):
        """Take screenshots of Reddit post and comments"""
        print(f"Taking screenshots for post: {post_id}")
        
        screenshots = {}
        
        try:
            driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Robust post screenshot
            post_selectors = [
                "[data-testid='post-content']", ".Post", "[data-click-id='text']", ".s1b7hvcc-0",
                "div[data-test-id='post-content']", "article", "main", "body"
            ]
            
            post_element = None
            for selector in post_selectors:
                try:
                    post_element = WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if post_element:
                        break
                except TimeoutException:
                    continue
            
            if post_element:
                post_filename = f"post_{post_id}.png"
                post_path = os.path.join(self.screenshots_dir, post_filename)
                try:
                    post_element.screenshot(post_path)
                    screenshots['post'] = post_path
                    print(f"Post screenshot saved: {post_filename}")
                except Exception as e:
                    print(f"Element screenshot failed: {e}, trying full page.")
            if 'post' not in screenshots:
                # Fallback: full page screenshot
                fallback_path = os.path.join(self.screenshots_dir, f"post_{post_id}_full.png")
                driver.save_screenshot(fallback_path)
                screenshots['post'] = fallback_path
                print(f"Full page screenshot saved: post_{post_id}_full.png")
            
            # Robust comment screenshots
            if comment_ids:
                # Wait for at least one comment to be present
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='comment']"))
                )
                all_comment_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='comment']")
                for i, comment_id in enumerate(comment_ids):
                    found = False
                    for elem in all_comment_elements:
                        # Try to match by id or data-comment-id attribute
                        elem_id = elem.get_attribute("id")
                        data_comment_id = elem.get_attribute("data-comment-id")
                        if (elem_id and elem_id.endswith(comment_id)) or (data_comment_id == comment_id):
                            comment_filename = f"comment_{comment_id}.png"
                            comment_path = os.path.join(self.screenshots_dir, comment_filename)
                            elem.screenshot(comment_path)
                            screenshots[f'comment_{i}'] = comment_path
                            print(f"Comment screenshot saved: {comment_filename}")
                            found = True
                            break
                    if not found:
                        print(f"Could not find comment element for {comment_id}, falling back to first available comment block.")
                        # Fallback: screenshot the i-th comment block if available
                        if i < len(all_comment_elements):
                            fallback_elem = all_comment_elements[i]
                            comment_filename = f"comment_{comment_id}_fallback.png"
                            comment_path = os.path.join(self.screenshots_dir, comment_filename)
                            fallback_elem.screenshot(comment_path)
                            screenshots[f'comment_{i}'] = comment_path
                            print(f"Fallback comment screenshot saved: {comment_filename}")
                        else:
                            # Last resort: full page
                            fallback_path = os.path.join(self.screenshots_dir, f"comment_{comment_id}_full.png")
                            driver.save_screenshot(fallback_path)
                            screenshots[f'comment_{i}'] = fallback_path
                            print(f"Full page fallback for comment: {comment_id}")
        
        except Exception as e:
            print(f"Error taking screenshots: {e}")
        
        return screenshots
    
    def create_video(self, post_data, comments_data, screenshots, audio_files):
        """Create video from screenshots and audio"""
        print("Creating video...")
        
        clips = []
        
        try:
            # Add post clip
            if 'post' in screenshots and 'post' in audio_files and audio_files['post']:
                try:
                    post_audio = AudioFileClip(audio_files['post'])
                    post_img = ImageClip(screenshots['post']).set_duration(post_audio.duration)
                    post_clip = post_img.set_audio(post_audio)
                    clips.append(post_clip)
                except Exception as e:
                    print(f"Error creating post clip: {e}")
            
            # Add comment clips
            for i, comment in enumerate(comments_data):
                comment_key = f'comment_{i}'
                if comment_key in screenshots and comment_key in audio_files and audio_files[comment_key]:
                    try:
                        comment_audio = AudioFileClip(audio_files[comment_key])
                        comment_img = ImageClip(screenshots[comment_key]).set_duration(comment_audio.duration)
                        comment_clip = comment_img.set_audio(comment_audio)
                        clips.append(comment_clip)
                    except Exception as e:
                        print(f"Error creating comment clip {i}: {e}")
            
            if not clips:
                print("No clips to process!")
                return None
            
            # Concatenate all clips
            main_video = concatenate_videoclips(clips, method="compose")
            
            # Add background video if available
            background_files = [f for f in os.listdir(self.background_dir) if f.endswith('.mp4')]
            
            if background_files:
                background_file = random.choice(background_files)
                background_path = os.path.join(self.background_dir, background_file)
                
                try:
                    background = VideoFileClip(background_path)
                    
                    # Loop background if needed
                    if background.duration < main_video.duration:
                        background = background.loop(duration=main_video.duration)
                    else:
                        background = background.subclip(0, main_video.duration)
                    
                    # Resize main video and overlay on background
                    main_video_resized = main_video.resize(height=background.h//2).set_position(('center', 'center'))
                    final_video = CompositeVideoClip([background, main_video_resized])
                    
                    background.close()
                    
                except Exception as e:
                    print(f"Error adding background: {e}")
                    final_video = main_video
            else:
                print("No background videos found, using main video only")
                final_video = main_video
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"reddit_video_{post_data['id']}_{timestamp}.mp4"
            output_path = os.path.join(self.videos_dir, output_filename)
            
            # Write video file
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Clean up clips
            for clip in clips:
                clip.close()
            main_video.close()
            final_video.close()
            
            print(f"Video saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating video: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            # Clean up audio files
            for file in os.listdir(self.audio_dir):
                if file.endswith('.wav'):
                    os.remove(os.path.join(self.audio_dir, file))
            
            # Clean up screenshot files
            for file in os.listdir(self.screenshots_dir):
                if file.endswith('.png'):
                    os.remove(os.path.join(self.screenshots_dir, file))
                    
            print("Temporary files cleaned up")
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")
    
    def generate_and_upload_video(self, subreddit=None, auto_upload=None):
        """Main method to generate and optionally upload video"""
        print("Starting video generation...")
        
        if subreddit is None:
            subreddit = random.choice(self.TOP_STORY_SUBREDDITS)
        if auto_upload is None:
            auto_upload = self.auto_upload
        
        try:
            # Get Reddit post
            submission = self.get_reddit_post(subreddit)
            if not submission:
                return None
            
            # Get comments
            comments = self.get_comments(submission)
            if not comments:
                print("No suitable comments found!")
                return None
            
            # Generate audio files
            audio_files = {}
            
            # Generate TTS for post
            post_text = f"{submission.title}. {submission.selftext}" if submission.selftext else submission.title
            audio_files['post'] = self.text_to_speech(post_text, f"post_{submission.id}")
            
            # Generate TTS for comments
            for i, comment in enumerate(comments):
                audio_file = self.text_to_speech(
                    comment['body'], 
                    f"comment_{comment['id']}"
                )
                if audio_file:
                    audio_files[f'comment_{i}'] = audio_file
            
            # Take screenshots
            driver = None
            try:
                driver = self.setup_browser()
                comment_ids = [comment['id'] for comment in comments]
                screenshots = self.take_screenshot(
                    driver, 
                    f"https://reddit.com{submission.permalink}", 
                    submission.id,
                    comment_ids
                )
            except Exception as e:
                print(f"Error with browser operations: {e}")
                screenshots = {}
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
            
            if not screenshots:
                print("No screenshots were taken. Cannot create video.")
                return None
            
            # Prepare post data
            post_data = {
                'id': submission.id,
                'title': submission.title,
                'text': submission.selftext,
                'url': submission.permalink,
                'subreddit': getattr(submission, 'subreddit_name', subreddit)
            }
            
            # Create video
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
            
            # Ask user about YouTube upload
            while True:
                try:
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
                except KeyboardInterrupt:
                    print("\nSkipping YouTube upload.")
                    break
            
            # Mark post as processed
            self.processed_posts.add(submission.id)
            self.save_processed_posts()
            
            # Clean up temporary files
            self.cleanup_temp_files()
            
            print(f"✅ Process complete!")
            return result
            
        except Exception as e:
            print(f"Error in video generation process: {e}")
            return None

def main():
    """Main function"""
    import argparse
    parser = argparse.ArgumentParser(description="Reddit Story Video Generator")
    parser.add_argument('--auto-upload', action='store_true', help='Automatically upload to YouTube without prompt')
    args = parser.parse_args()
    try:
        generator = RedditVideoGenerator(auto_upload=args.auto_upload)
        result = generator.generate_and_upload_video(auto_upload=args.auto_upload)
        if result:
            print(f"\nSuccess! Video saved at: {result['video_path']}")
            if 'video_url' in result:
                print(f"YouTube URL: {result['video_url']}")
        else:
            print("Failed to generate video")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()