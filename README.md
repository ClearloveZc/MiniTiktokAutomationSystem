# TikTok Auto Publisher 🎬

A Selenium-based automation tool for posting videos to TikTok. Supports headless operation in Docker containers.

## Features

- 🔐 Automatic login via Chrome user data or cookies
- 📹 Automated video upload
- 📝 Custom titles and hashtags
- 🐳 Docker support for headless operation
- 🛡️ Anti-detection measures using undetected-chromedriver

## Quick Start

### Prerequisites

- Python 3.10+
- Google Chrome browser
- (Optional) Docker for containerized deployment

### Installation

1. **Clone and setup**
   ```bash
   cd tiktokAuto
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Usage

#### Basic Usage

```bash
# Upload a video with title and tags
python src/main.py -v data/videos/my_video.mp4 -t "Check this out!" --tags fyp viral tiktok

# Run in headless mode
python src/main.py -v data/videos/my_video.mp4 -t "My Video" --headless
```

#### First Time Login

On first run, the browser will open for you to login manually. Your session will be saved for future runs.

```bash
# Just run with any video to trigger login
python src/main.py -v data/videos/test.mp4
```

#### Command Line Options

| Option | Description |
|--------|-------------|
| `-v, --video` | Path to video file (required) |
| `-t, --title` | Video title/caption |
| `--tags` | Hashtags (space separated, without #) |
| `--headless` | Run in headless mode |
| `-c, --config` | Custom config file path |

### Docker Usage

Docker deployment uses a remote Selenium Chrome container for reliable headless operation.

#### Step 1: Export Cookies (First time only)

Run this **locally** to login and export cookies:

```bash
source venv/bin/activate
python src/export_cookies.py
# Browser opens → Login to TikTok → Press Enter
```

Cookies are saved to `data/cookies/tiktok_cookies.json`

#### Step 2: Build and Run in Docker

```bash
cd docker
docker-compose build

# Run with a video
docker-compose run tiktok-auto python src/main.py \
  -v /app/data/videos/my_video.mp4 \
  -t "Uploaded from Docker!" \
  --tags docker automation

# Stop services when done
docker-compose down
```

#### Cookie Refresh

If login expires, just re-run `python src/export_cookies.py` locally.

## Project Structure

```
tiktokAuto/
├── src/
│   ├── main.py          # Entry point
│   ├── browser.py       # Browser management
│   ├── login.py         # Login handling
│   ├── uploader.py      # Video upload logic
│   ├── export_cookies.py # Cookie export tool
│   ├── login_only.py    # Manual login helper
│   ├── open_browser.py  # Open browser to view results
│   └── utils.py         # Utilities
├── config/
│   └── config.yaml      # Configuration
├── data/
│   ├── videos/          # Videos to upload
│   └── cookies/         # Session cookies (for Docker)
├── chrome_data/         # Chrome user data (for local)
├── docker/
│   ├── Dockerfile.simple
│   └── docker-compose.yml
└── logs/                # Application logs
```

## Configuration

Edit `config/config.yaml` to customize:

- Browser settings (window size, headless mode)
- Timing delays (for human-like behavior)
- Upload settings (timeouts, retries)
- Logging preferences

## Troubleshooting

### Login Issues
- Delete `chrome_data/` folder and login again
- Or delete `data/cookies/tiktok_cookies.json`

### Upload Fails
- Check `logs/tiktok_auto.log` for details
- Ensure video format is supported (mp4, mov, webm)
- Try running without headless mode to see what's happening

### Docker Issues
- Increase `shm_size` in docker-compose.yml if Chrome crashes
- Ensure volumes are mounted correctly

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with TikTok's Terms of Service. Automated posting may violate platform rules.

## License

MIT License
