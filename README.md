# KURO Studio — Phase 1 Foundation

Free-first gaming YouTube studio built from scratch. No existing website is required to convert.

## Included
- KURO chat using Gemini API (optional `GEMINI_API_KEY`)
- Public YouTube search using optional `YOUTUBE_API_KEY`
- Thumbnail design from uploaded screenshots with text overlay
- Locally created abstract thumbnail backgrounds
- Basic MP4 normalization using FFmpeg when available
- Video blueprint generator and editor-aware instructions

## Deploy on Streamlit Community Cloud
1. Create a new GitHub repository (e.g. `kuro-studio`).
2. Upload `app.py`, `requirements.txt`, and `README.md` to the repository root.
3. Deploy the repository on Streamlit Community Cloud, entry file `app.py`.
4. In app settings → Secrets, add:
   ```toml
   GEMINI_API_KEY = "your_key"
   YOUTUBE_API_KEY = "optional_key"
   ```
5. Create a Gemini key at https://aistudio.google.com/apikey.
6. Never commit real keys to GitHub.

## Run locally on a PC
Install Python 3.10+ and FFmpeg, make sure `ffmpeg` is on PATH, then:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limitations
- Cloud FFmpeg may not be installed or may hit resource limits.
- Video processing is basic normalization, not AI highlight detection or automatic montage editing.
- Abstract thumbnails are generated locally and are not AI-generated official game art.
- Private YouTube analytics require a future authorized OAuth integration.
- Free API availability, quotas, and terms can change.
