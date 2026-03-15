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
             with st.spinner("Extracting audio with yt-dlp… this may take a moment."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        output_template = os.path.join(tmpdir, "audio")

                        # ── Step 1: download audio with yt-dlp ──────────────────
                        proc = subprocess.run(
                            [
                                "yt-dlp",
                                "--extract-audio",
                                "--audio-format", "mp3",
                                "--audio-quality", "0",
                                "-o", f"{output_template}.%(ext)s",
                                url.strip(),
                            ],
                            capture_output=True,
                            text=True,
                        )

                        if proc.returncode != 0:
                            st.error(
                                "🚨 **Instagram blocked the download.** \n\n"
                                "Since this app is running in the cloud, Instagram often blocks requests asking for a login. "
                                "Please use the **Upload File** tab instead."
                            )
                            with st.expander("Show detailed error log"):
                                st.code(proc.stderr.strip())
                            st.stop()

                        # ── Step 2: locate the downloaded file ──────────────────
                        files = glob.glob(os.path.join(tmpdir, "audio.*"))
                        if not files:
                            st.error("No audio file was created. Check the URL and try again.")
                            st.stop()

                        audio_path = files[0]

                        # ── Step 3: identify with ShazamAPI ─────────────────────
                        identify_music_from_file_path(audio_path)

                except FileNotFoundError:
                    st.error(
                        "`yt-dlp` was not found on your system. "
                        "Install it with `pip install yt-dlp` or `brew install yt-dlp`."
                    )
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
