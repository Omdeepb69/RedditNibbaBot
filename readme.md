# 🤖 RedditNibbaBot 

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-red.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/status-ACTIVE-green.svg?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow.svg?style=for-the-badge)

**⚡ AUTOMATED REDDIT-TO-YOUTUBE CONTENT PIPELINE ⚡**

*"Sometimes you gotta run before you can walk." - Tony Stark*

</div>

---

## 🚀 MISSION BRIEFING

Welcome to **RedditNibbaBot** - the ultimate automated content generation system that transforms Reddit's hottest stories into engaging YouTube videos. Built with the precision of Stark Industries and the efficiency of J.A.R.V.I.S.

### 🎯 CORE CAPABILITIES

- **🔍 INTELLIGENCE GATHERING** - Automatically scans Reddit for trending content
- **🎤 VOICE SYNTHESIS** - Converts text to natural speech using advanced TTS
- **📸 VISUAL CAPTURE** - Takes high-quality screenshots of posts and comments  
- **🎬 VIDEO PRODUCTION** - Creates cinematic videos with background footage
- **📺 YOUTUBE DEPLOYMENT** - Automatically uploads with SEO-optimized metadata
- **🧠 SMART FILTERING** - Avoids duplicates and inappropriate content

---

## 🛠️ SYSTEM REQUIREMENTS

```bash
# Core Dependencies
python >= 3.8
selenium >= 4.0
moviepy >= 1.0.3
praw >= 7.0
pyttsx3 >= 2.90
google-api-python-client >= 2.0
```

### 🔧 HARDWARE SPECS
- **RAM**: 4GB+ (8GB recommended for smooth operation)
- **Storage**: 2GB+ free space for video processing
- **Network**: Stable internet connection for API calls

---

## ⚙️ INSTALLATION PROTOCOL

### Step 1: Clone the Repository
```bash
git clone https://github.com/Omdeepb69/redditNibbaBot.git
cd redditNibbaBot
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: System Configuration
```bash
# Install Firefox (required for screenshots)
# Ubuntu/Debian:
sudo apt-get install firefox

# macOS:
brew install firefox

# Windows: Download from Firefox website
```

---

## 🔐 API AUTHENTICATION

### Reddit API Setup
1. Visit [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Create a new application (script type)
3. Note your `client_id` and `client_secret`

### YouTube API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → Enable YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Download `client_secret.json`

### Environment Configuration
Create `.env` file:
```env
YOUR_CLIENT_ID=your_reddit_client_id
YOUR_CLIENT_SECRET=your_reddit_client_secret
```

---

## 🚀 DEPLOYMENT SEQUENCE

### Quick Start
```bash
python main.py
```

### Advanced Configuration
```python
generator = RedditVideoGenerator()

# Generate video from specific subreddit
result = generator.generate_and_upload_video("AskReddit")

# Process multiple posts
for i in range(5):
    generator.generate_and_upload_video("tifu")
```

---

## 📁 PROJECT STRUCTURE

```
redditNibbaBot/
├── 🤖 main.py                 # Core bot logic
├── 📄 requirements.txt        # Dependencies
├── 🔐 .env                    # API credentials
├── 🔑 client_secret.json      # YouTube OAuth
├── 📂 audio/                  # Generated TTS files
├── 📂 screenshots/            # Reddit captures
├── 📂 videos/                 # Final output
├── 📂 background_videos/      # Background footage
└── 📊 processed_posts.json    # Tracking file
```

---

## 🎛️ CONTROL PANEL

### Subreddit Targeting
```python
# Popular choices for maximum engagement
subreddits = [
    "AskReddit",      # Questions & Stories
    "tifu",           # Funny failures  
    "relationships",  # Drama content
    "nosleep",        # Horror stories
    "confession"      # Personal stories
]
```

### Video Customization
```python
# Adjust these parameters in main.py
MAX_COMMENTS = 5        # Comments per video
MAX_WORDS = 100        # Comment length limit
TTS_RATE = 150         # Speech speed
VIDEO_FPS = 24         # Output quality
```

---

## 🎯 TARGETING ALGORITHM

The bot uses advanced filtering to select optimal content:

- **✅ HIGH ENGAGEMENT** - Posts with 1000+ upvotes
- **✅ FRESH CONTENT** - Less than 24 hours old
- **✅ SFW ONLY** - Family-friendly content
- **✅ TEXT BASED** - Rich storytelling content
- **❌ DUPLICATE FILTER** - Never processes same post twice

---

## 📈 PERFORMANCE METRICS

### Typical Output Stats
- **Video Length**: 2-8 minutes
- **Processing Time**: 5-10 minutes per video
- **Success Rate**: 95%+ with proper setup
- **Upload Speed**: 2-5 minutes to YouTube

### Optimization Tips
- Use SSD storage for faster video processing
- Close unnecessary applications during generation
- Ensure stable internet for seamless uploads

---

## 🛡️ SAFETY PROTOCOLS

### Content Filtering
- Automatic NSFW detection and rejection
- Spam comment filtering
- Duplicate prevention system
- Manual upload confirmation

### Error Handling
- Robust retry mechanisms for API failures
- Graceful degradation on missing dependencies
- Comprehensive logging for debugging

---

## 🔧 TROUBLESHOOTING

### Common Issues & Solutions

**❌ "Firefox not found"**
```bash
# Install Firefox browser
# Add Firefox to system PATH
```

**❌ "Reddit API Authentication Failed"**
```bash
# Verify credentials in .env file
# Check Reddit app permissions
```

**❌ "YouTube Upload Failed"**
```bash
# Re-authenticate with fresh token
# Check internet connection
# Verify video file isn't corrupted
```

---

## 🚀 ADVANCED FEATURES

### Background Video Integration
Add your own background videos to `/background_videos/` folder for dynamic visuals.

### Custom Voice Selection
Modify TTS settings for different voice styles:
```python
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Try different voices
```

### Batch Processing
Run multiple instances for 24/7 content generation:
```bash
# Schedule with cron
0 */6 * * * /usr/bin/python3 /path/to/redditNibbaBot/main.py
```

---

## 📊 ANALYTICS INTEGRATION

Track your bot's performance:
- Monitor YouTube video metrics
- Track Reddit engagement rates  
- Analyze optimal posting times
- A/B test different subreddits

---

## 🤝 CONTRIBUTING

Want to enhance the bot? Here's how:

1. **🍴 Fork** the repository
2. **🌿 Create** feature branch (`git checkout -b feature/AmazingFeature`)
3. **💾 Commit** changes (`git commit -m 'Add AmazingFeature'`)
4. **📤 Push** to branch (`git push origin feature/AmazingFeature`)
5. **🔄 Open** Pull Request

---

## 📜 LICENSE

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🏆 ACKNOWLEDGMENTS

- **Reddit API** - For providing the content source
- **YouTube API** - For seamless video hosting
- **MoviePy** - For powerful video processing
- **Selenium** - For web automation magic

---

## 📞 SUPPORT

**Created by**: [@Omdeepb69](https://github.com/Omdeepb69)

Having issues? Create an issue or reach out:
- 🐛 [Report Bug](https://github.com/Omdeepb69/redditNibbaBot/issues)
- 💡 [Request Feature](https://github.com/Omdeepb69/redditNibbaBot/issues)
- 💬 [Discussions](https://github.com/Omdeepb69/redditNibbaBot/discussions)

---

<div align="center">

**⚡ POWERED BY STARK TECHNOLOGY ⚡**

*"The best weapon is the one you never have to fire. But this bot fires content 24/7."*

![Stark Industries](https://img.shields.io/badge/STARK-INDUSTRIES-gold.svg?style=for-the-badge)

**[⭐ Star this repo if it helped you! ⭐](https://github.com/Omdeepb69/redditNibbaBot)**

</div>