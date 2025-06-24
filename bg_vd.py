import yt_dlp
import os
import sys
from pathlib import Path
import re

class YouTubeDownloader:
    def __init__(self, download_path="background_videos"):
        """
        Initialize YouTube downloader
        
        Args:
            download_path (str): Directory to save downloaded videos
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        
        # Default options for yt-dlp
        self.ydl_opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'format': 'best[height<=1080]',  # Download best quality up to 1080p
            'noplaylist': True,  # Don't download entire playlist by default
        }
    
    def validate_url(self, url):
        """
        Validate if the URL is a valid YouTube URL
        
        Args:
            url (str): YouTube URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return youtube_regex.match(url) is not None
    
    def get_video_info(self, url):
        """
        Get video information without downloading
        
        Args:
            url (str): YouTube URL
            
        Returns:
            dict: Video information or None if error
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': len(info.get('formats', []))
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def download_video(self, url, quality='best', audio_only=False, video_only=False):
        """
        Download video from YouTube URL
        
        Args:
            url (str): YouTube URL
            quality (str): Video quality ('best', 'worst', '720p', '480p', etc.)
            audio_only (bool): Download only audio
            video_only (bool): Download only video (no audio)
            
        Returns:
            str: Path to downloaded file or None if failed
        """
        if not self.validate_url(url):
            print("Invalid YouTube URL!")
            return None
        
        if audio_only:
            format_selector = 'bestaudio/best'
            self.ydl_opts['outtmpl'] = str(self.download_path / '%(title)s.%(ext)s')
        elif video_only:
            format_selector = 'bestvideo/best'
            self.ydl_opts['outtmpl'] = str(self.download_path / '%(title)s.%(ext)s')
        else:
            if quality == 'best':
                format_selector = 'best[height<=1080]'
            elif quality == 'worst':
                format_selector = 'worst'
            elif quality.endswith('p'):
                height = quality[:-1]
                format_selector = f'best[height<={height}]'
            else:
                format_selector = quality
        
        self.ydl_opts['format'] = format_selector
        
        try:
            print(f"Downloading video from: {url}")
            print(f"Quality: {quality}")
            print(f"Audio only: {audio_only}")
            print(f"Video only: {video_only}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video')
                
                print(f"Title: {title}")
                print("Starting download...")
                
                ydl.download([url])
                
                for file in self.download_path.iterdir():
                    if file.is_file() and title.replace('/', '_') in str(file):
                        print(f"✅ Download completed: {file}")
                        return str(file)
                
                print("✅ Download completed!")
                return "Downloaded successfully"
                
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return None
    
    def download_playlist(self, url, max_downloads=None):
        """
        Download entire playlist
        
        Args:
            url (str): YouTube playlist URL
            max_downloads (int): Maximum number of videos to download
            
        Returns:
            bool: True if successful, False otherwise
        """
        playlist_opts = self.ydl_opts.copy()
        playlist_opts['noplaylist'] = False
        
        if max_downloads:
            playlist_opts['playlistend'] = max_downloads
        
        try:
            print(f"Downloading playlist from: {url}")
            
            with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                ydl.download([url])
            
            print("✅ Playlist download completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading playlist: {e}")
            return False
    
    def download_audio_only(self, url, format='mp3'):
        """
        Download only audio from video
        
        Args:
            url (str): YouTube URL
            format (str): Audio format ('mp3', 'wav', 'm4a', etc.)
            
        Returns:
            str: Path to downloaded audio file or None if failed
        """
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '192',
            }],
        }
        
        try:
            print(f"Downloading audio only from: {url}")
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([url])
            
            print("✅ Audio download completed!")
            return "Audio downloaded successfully"
            
        except Exception as e:
            print(f"❌ Error downloading audio: {e}")
            return None
    
    def list_formats(self, url):
        """
        List all available formats for a video
        
        Args:
            url (str): YouTube URL
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                print(f"\nAvailable formats for: {info.get('title', 'Unknown')}")
                print("-" * 80)
                print(f"{'Format ID':<12} {'Extension':<10} {'Resolution':<12} {'Note':<30}")
                print("-" * 80)
                
                for format_info in info.get('formats', []):
                    format_id = format_info.get('format_id', 'N/A')
                    ext = format_info.get('ext', 'N/A')
                    resolution = format_info.get('resolution', 'audio only')
                    note = format_info.get('format_note', '')
                    
                    print(f"{format_id:<12} {ext:<10} {resolution:<12} {note:<30}")
                    
        except Exception as e:
            print(f"Error listing formats: {e}")

def main():
    """
    Main function with interactive menu
    """
    downloader = YouTubeDownloader()
    
    print("🎥 YouTube Video Downloader")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Download video (best quality)")
        print("2. Download video (custom quality)")
        print("3. Download audio only")
        print("4. Download playlist")
        print("5. Get video info")
        print("6. List available formats")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            url = input("Enter YouTube URL: ").strip()
            if url:
                downloader.download_video(url)
        
        elif choice == '2':
            url = input("Enter YouTube URL: ").strip()
            quality = input("Enter quality (720p, 480p, best, worst): ").strip()
            if url:
                downloader.download_video(url, quality=quality)
        
        elif choice == '3':
            url = input("Enter YouTube URL: ").strip()
            format_type = input("Enter audio format (mp3, wav, m4a) [default: mp3]: ").strip() or 'mp3'
            if url:
                downloader.download_audio_only(url, format=format_type)
        
        elif choice == '4':
            url = input("Enter YouTube playlist URL: ").strip()
            max_downloads = input("Max downloads (press Enter for all): ").strip()
            max_downloads = int(max_downloads) if max_downloads.isdigit() else None
            if url:
                downloader.download_playlist(url, max_downloads)
        
        elif choice == '5':
            url = input("Enter YouTube URL: ").strip()
            if url:
                info = downloader.get_video_info(url)
                if info:
                    print(f"\nVideo Information:")
                    print(f"Title: {info['title']}")
                    print(f"Uploader: {info['uploader']}")
                    print(f"Duration: {info['duration']} seconds")
                    print(f"Views: {info['view_count']:,}")
                    print(f"Upload Date: {info['upload_date']}")
                    print(f"Available Formats: {info['formats']}")
                    print(f"Description: {info['description']}")
        
        elif choice == '6':
            url = input("Enter YouTube URL: ").strip()
            if url:
                downloader.list_formats(url)
        
        elif choice == '7':
            print("Goodbye! 👋")
            break
        
        else:
            print("Invalid choice! Please select 1-7.")

def simple_download_example():
    """
    Simple example of how to use the downloader
    """
    downloader = YouTubeDownloader("my_downloads")
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  
    downloader.download_video(url)
    
    
    downloader.download_audio_only(url, format='mp3')
    
    info = downloader.get_video_info(url)
    if info:
        print(f"Video title: {info['title']}")

if __name__ == "__main__":
    # Run the interactive menu
    main()
    
    # Uncomment to run simple example instead
    # simple_download_example()
    
    """
    from youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader("downloads")

# Download video
downloader.download_video("https://www.youtube.com/watch?v=VIDEO_ID")

# Download audio only
downloader.download_audio_only("https://www.youtube.com/watch?v=VIDEO_ID", format='mp3')

# Get video info
info = downloader.get_video_info("https://www.youtube.com/watch?v=VIDEO_ID")
print(info)

"""