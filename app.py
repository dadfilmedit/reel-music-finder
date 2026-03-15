import streamlit as st
import tempfile
import os
import subprocess
import glob

st.set_page_config(
    page_title="Instagram Reel Music Finder",
    page_icon="🎵",
    layout="centered",
)

st.title("🎵 Instagram Reel Music Finder")
st.write("Identify the music from an Instagram Reel. You can either paste a link, or if Instagram blocks the link, simply upload the video directly.")

tab1, tab2 = st.tabs(["🔗 Paste Link", "📁 Upload File (Most Reliable)"])

def identify_music_from_file_path(audio_path):
    from ShazamAPI import Shazam
    
    with open(audio_path, "rb") as f:
        mp3_data = f.read()

    shazam = Shazam(mp3_data)
    recognize_generator = shazam.recognizeSong()

    track = None
    try:
        _offset, result = next(recognize_generator)
        if result and "track" in result:
            track = result["track"]
    except StopIteration:
        pass

    if track:
        song   = track.get("title",    "Unknown Song")
        artist = track.get("subtitle", "Unknown Artist")

        st.success("✅ Music identified!")
        st.markdown(f"# 🎵 {song}")
        st.markdown(f"# 🎤 {artist}")

        # Optional: show album art if available
        images = track.get("images", {})
        cover  = images.get("coverarthq") or images.get("coverart")
        if cover:
            st.image(cover, width=300)
    else:
        st.warning(
            "Shazam could not identify the music in this audio track. "
            "Try a video where the music is more prominent."
        )

# ── TAB 1: PASTE LINK ────────────────────────────────────────────────────────
with tab1:
    url = st.text_input(
        "Instagram Reel URL",
        placeholder="https://www.instagram.com/reel/...",
    )

    if st.button("Find Music from Link", type="primary", use_container_width=True):
        if not url.strip():
             st.warning("Please enter an Instagram Reel URL.")
        else:
             with st.spinner("Extracting audio with RapidAPI… this may take a moment."):
                try:
                    if "RAPIDAPI_KEY" not in st.secrets:
                        st.error("🚨 **RapidAPI Key Missing** \n\nStreamlit Cloud's IP address is blocked by Instagram. To use the Link feature, you must configure a free RapidAPI key.\n\n**How to fix this in 60 seconds:**\n1. Go to [RapidAPI - Instagram Scraper API by Social API](https://rapidapi.com/social-api/api/instagram-scraper-api2/pricing) and subscribe to the **Basic (Free)** tier (500 requests/month).\n2. Go to the [Endpoints tab](https://rapidapi.com/social-api/api/instagram-scraper-api2) and copy your `X-RapidAPI-Key` from the code snippet on the right.\n3. Go to your Streamlit Cloud Dashboard, click **⋮ Settings** -> **Secrets**.\n4. Paste: `RAPIDAPI_KEY = \"your_key_here\"` and click Save.\n\n*Alternatively, use the **Upload File** tab right now!*")
                        st.stop()
                    
                    # ── Step 1: get video JSON from RapidAPI ──────────────────
                    import requests
                    api_url = "https://instagram-scraper-api2.p.rapidapi.com/v1/post_info"
                    querystring = {"code_or_id_or_url": url.strip()}
                    headers = {
                        "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
                        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
                    }
                    
                    response = requests.get(api_url, headers=headers, params=querystring)
                    
                    if response.status_code != 200:
                        st.error(f"🚨 **API Error {response.status_code}**\n\nPlease check your RapidAPI key or the URL.")
                        with st.expander("Show detailed API log"):
                            st.code(response.text)
                        st.stop()
                        
                    data = response.json()
                    
                    # Extract the first video URL
                    video_url = None
                    try:
                        # Depending on the exact schema, it usually sits here for a reel:
                        items = data.get("data", {}).get("items", [])
                        if not items and "data" in data and "video_versions" in data["data"]:
                            video_url = data["data"]["video_versions"][0]["url"]
                        elif items:
                            item = items[0]
                            if "video_versions" in item:
                                video_url = item["video_versions"][0]["url"]
                            elif "carousel_media" in item:
                                # For carousel with a video
                                for c_media in item["carousel_media"]:
                                    if "video_versions" in c_media:
                                        video_url = c_media["video_versions"][0]["url"]
                                        break
                    except Exception as e:
                        st.error(f"Failed to parse Instagram data. Please use the Upload File tab. Details: {e}")
                        st.stop()
                        
                    if not video_url:
                        st.error("No video found in this Instagram link. Make sure it's a valid Reel or Video post.")
                        st.stop()
                        
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # ── Step 2: download the raw video file ──────────────────
                        temp_video_path = os.path.join(tmpdir, "downloaded_video.mp4")
                        with requests.get(video_url, stream=True) as r:
                            r.raise_for_status()
                            with open(temp_video_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                    
                        # ── Step 3: extract audio using ffmpeg ──────────────────
                        output_audio_path = os.path.join(tmpdir, "extracted_audio.mp3")
                        proc = subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-i", temp_video_path,
                                "-vn",
                                "-acodec", "libmp3lame",
                                "-q:a", "2",
                                output_audio_path
                            ],
                            capture_output=True,
                            text=True,
                        )
                        
                        if proc.returncode != 0:
                            st.error("Failed to extract audio from the downloaded Instagram video.")
                            with st.expander("Show detailed error log"):
                                st.code(proc.stderr.strip())
                            st.stop()

                        # ── Step 4: identify with ShazamAPI ─────────────────────
                        identify_music_from_file_path(output_audio_path)

                except Exception as exc:
                    st.error(f"An unexpected error occurred: {exc}")

# ── TAB 2: UPLOAD FILE ───────────────────────────────────────────────────────
with tab2:
    st.info("💡 **Why upload?** Instagram regularly blocks cloud servers from downloading Reels without logging in. Downloading the video to your phone/computer and uploading it here will bypass Instagram's security 100% of the time.")
    
    uploaded_file = st.file_uploader(
        "Upload an Instagram Reel Video (MP4) or Audio (MP3/WAV)",
        type=["mp4", "mp3", "wav", "m4a", "mov"]
    )
    
    if st.button("Find Music from File", type="primary", use_container_width=True):
        if not uploaded_file:
            st.warning("Please upload a file first.")
        else:
            with st.spinner("Identifying music…"):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        # Save uploaded file to temp dir
                        file_ext = os.path.splitext(uploaded_file.name)[1]
                        temp_file_path = os.path.join(tmpdir, f"uploaded_video{file_ext}")
                        
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # We don't need to extract MP3 out of MP4 if we use ShazamAPI!
                        # ShazamAPI actually requires raw audio bytes, but ffmpeg might be safer 
                        # to ensure the input format is strictly a compressed audio format it likes.
                        
                        # Let's use yt-dlp or ffmpeg to extract just audio from the uploaded video
                        output_audio_path = os.path.join(tmpdir, "extracted_audio.mp3")
                        
                        proc = subprocess.run(
                            [
                                "ffmpeg",
                                "-y",  # Overwrite output without asking
                                "-i", temp_file_path,
                                "-vn",  # no video
                                "-acodec", "libmp3lame",
                                "-q:a", "2",
                                output_audio_path
                            ],
                            capture_output=True,
                            text=True,
                        )
                        
                        if proc.returncode != 0:
                            st.error("Failed to extract audio from the uploaded file.")
                            with st.expander("Show detailed error log"):
                                st.code(proc.stderr.strip())
                            st.stop()

                        # Identify with ShazamAPI
                        identify_music_from_file_path(output_audio_path)
                        
                except Exception as exc:
                    st.error(f"An unexpected error occurred: {exc}")
