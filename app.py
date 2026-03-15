import streamlit as st
import asyncio
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
st.write("Paste an Instagram Reel URL below to identify the music.")

url = st.text_input(
    "Instagram Reel URL",
    placeholder="https://www.instagram.com/reel/...",
)

if st.button("Find Music", type="primary", use_container_width=True):
    if not url.strip():
        st.warning("Please enter an Instagram Reel URL.")
    else:
        with st.spinner("Extracting audio and identifying music… this may take a moment."):
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
                            f"yt-dlp failed to download the reel. Make sure the URL is public "
                            f"and that yt-dlp is installed.\n\n```\n{proc.stderr.strip()}\n```"
                        )
                        st.stop()

                    # ── Step 2: locate the downloaded file ──────────────────
                    files = glob.glob(os.path.join(tmpdir, "audio.*"))
                    if not files:
                        st.error("No audio file was created. Check the URL and try again.")
                        st.stop()

                    audio_path = files[0]

                    # ── Step 3: identify with Shazam ────────────────────────
                    from shazamio import Shazam  # imported here so Streamlit loads fast

                    async def identify(path: str) -> dict:
                        shazam = Shazam()
                        return await shazam.recognize(path)

                    result = asyncio.run(identify(audio_path))

                    # ── Step 4: display results ─────────────────────────────
                    if result and "track" in result:
                        track = result["track"]
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
                            "Shazam could not identify the music in this reel. "
                            "Try a reel where the music is more prominent."
                        )

            except FileNotFoundError:
                st.error(
                    "`yt-dlp` was not found on your system. "
                    "Install it with `pip install yt-dlp` or `brew install yt-dlp`."
                )
            except Exception as exc:
                st.error(f"An unexpected error occurred: {exc}")
