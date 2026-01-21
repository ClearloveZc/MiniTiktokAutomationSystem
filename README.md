# Mini TikTok Automation System 🎬

A Selenium-based automation tool for posting videos to TikTok.

## Features

- 🔐 Automatic login via Chrome user data
- 📹 Automated video upload with title and hashtags
- 🐳 Docker support for headless operation
- 🛡️ Anti-detection using undetected-chromedriver

## Quick Start (5 Steps)

```bash
# 1. Clone the project
git clone https://github.com/YOUR_USERNAME/MiniTiktokAutomationSystem.git
cd MiniTiktokAutomationSystem

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Login to TikTok (required, only once)
python src/login_only.py
# Browser opens → Login manually → Close browser

# 4. Upload a video
python src/main.py -v data/videos/example.mp4 -t "My Video" --tags fyp viral

# 5. View your uploads (optional)
python src/open_browser.py
```

**That's it!** 🎉

---

## Command Line Options

```bash
python src/main.py -v <video_path> -t <title> --tags <tag1> <tag2> [--headless]
```

| Option | Required | Description |
|--------|----------|-------------|
| `-v, --video` | ✅ | Path to video file |
| `-t, --title` | ❌ | Video title/caption |
| `--tags` | ❌ | Hashtags (without #, space separated) |
| `--headless` | ❌ | Run without browser window |

### Examples

```bash
# Simple upload
python src/main.py -v data/videos/example.mp4

# With title and tags
python src/main.py -v data/videos/example.mp4 -t "Check this out!" --tags fyp viral funny

# Headless mode (no browser window)
python src/main.py -v data/videos/example.mp4 -t "Auto post" --headless
```

---

## Docker Usage (Optional)

For server deployment or scheduled tasks.

### Step 1: Export Cookies (locally)

```bash
python src/export_cookies.py
# Browser opens → Login → Press Enter
```

### Step 2: Run in Docker

```bash
cd docker
docker-compose build

docker-compose run tiktok-auto python src/main.py \
  -v /app/data/videos/example.mp4 \
  -t "Uploaded from Docker" \
  --tags docker automation

docker-compose down
```

---

## Project Structure

```
MiniTiktokAutomationSystem/
├── src/
│   ├── main.py           # Entry point
│   ├── login_only.py     # Login helper (run this first!)
│   ├── open_browser.py   # View uploaded videos
│   ├── export_cookies.py # Export cookies for Docker
│   ├── browser.py        # Browser management
│   ├── login.py          # Login logic
│   ├── uploader.py       # Upload logic
│   └── utils.py          # Utilities
├── config/
│   └── config.yaml       # Configuration
├── data/
│   ├── videos/           # Put your videos here
│   └── cookies/          # Cookies (for Docker)
├── chrome_data/          # Browser session (auto-created)
├── docker/               # Docker files
└── logs/                 # Log files
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Login expired | Run `python src/login_only.py` again |
| Upload fails | Check `logs/tiktok_auto.log` |
| Browser not found | Install Google Chrome |
| Docker connection error | Wait a few seconds and retry |

---

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with TikTok's Terms of Service.

## License

MIT License
