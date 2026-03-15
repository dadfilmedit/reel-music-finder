# 🎵 Instagram Reel Music Finder

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

Instantly identify the music playing in any **public** Instagram Reel. Paste a URL, click a button — get the song title, artist, and album art in seconds.

---

## How It Works

1. **Download** — `yt-dlp` extracts the audio track from the Reel as an MP3
2. **Identify** — `shazamio` fingerprints the audio against the Shazam database
3. **Display** — Song title, artist name, and album artwork are shown instantly

---

## 🚀 Run Locally

### Prerequisites
- Python 3.10+
- `ffmpeg` installed (`brew install ffmpeg` on macOS)

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/reel-music-finder.git
cd reel-music-finder
pip install -r requirements.txt
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## ☁️ Deploy to Streamlit Cloud

1. Fork or push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"** → connect your GitHub account
4. Select this repo, set branch to `main`, and main file to `app.py`
5. Click **Deploy** — done!

> **Note:** `packages.txt` automatically installs `ffmpeg` on Streamlit Cloud's Linux environment.

---

## ⚠️ Limitations

- Only works with **public** Instagram Reels
- Music must be prominent enough for Shazam to identify it
- Instagram occasionally changes their CDN; if downloads fail, update `yt-dlp` via `pip install -U yt-dlp`

---

## 🛠 Tech Stack

| Tool | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web UI |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Audio download |
| [shazamio](https://github.com/dotX12/shazamio) | Music identification |
| ffmpeg | Audio conversion |

---

*Built by AntiGravity — South Florida's creative tech studio.*
