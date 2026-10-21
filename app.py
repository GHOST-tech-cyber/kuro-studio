import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

st.set_page_config(page_title="KURO Studio", page_icon="◈", layout="wide")

# KURO Phase 1: free-first foundation.
MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

SYSTEM_PROMPT = """
You are KURO, a practical Gaming & YouTube Studio assistant.
Help the creator choose games, research video opportunities from supplied evidence, design video
concepts, write hooks/scripts, plan editing, create thumbnail concepts, titles, descriptions, tags,
music direction, and publishing checklists.

Be friendly, direct, and practical. Ask at most one essential question at a time. If enough details
exist, make a useful first draft. Preserve exact game names; do not silently replace a custom title.
Never claim to have watched footage, verified trends, read comments, verified copyright, or accessed
private analytics unless that evidence/tool access is actually available. Do not invent statistics or
guarantee virality. Clearly distinguish evidence, assumptions, and creative recommendations.

For a full video package include:
- recommended concept and why it suits the creator's goal
- hook for the first 1-3 seconds
- timestamped script/scene plan
- footage/capture checklist
- editor recommendation based on device and budget
- specific scene-by-scene edit instructions, captions, cuts, sound effects and pacing
- music mood/search terms and a reminder to verify the exact track licence
- three title options, description, relevant tags/hashtags, thumbnail concept, CTA, export checklist
If the user hasn't provided footage and the app cannot inspect it, never pretend to have analyzed it.
"""

def get_secret(name):
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return os.getenv(name, "").strip()

def ask_kuro(messages, api_key, creator_context=""):
    if not api_key:
        return None, "KURO's AI brain is not connected yet. Add GEMINI_API_KEY in Streamlit Secrets when you have a free-tier key. The thumbnail tools and manual planning tools still work."
    contents = [{"role": "user" if m["role"] == "user" else "model",
                 "parts": [{"text": m["content"]}]} for m in messages]
    system = SYSTEM_PROMPT + (("\n\nCREATOR CONTEXT:\n" + creator_context) if creator_context else "")
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4500},
    }
    try:
        response = requests.post(GEMINI_URL, params={"key": api_key}, json=payload, timeout=60)
        data = response.json()
        if response.status_code != 200:
            return None, data.get("error", {}).get("message", f"AI service returned HTTP {response.status_code}")
        candidates = data.get("candidates", [])
        if not candidates:
            return None, "KURO received an empty response. Try again with a shorter message."
        parts = candidates[0].get("content", {}).get("parts", [])
        return "\n".join(part.get("text", "") for part in parts if part.get("text")), ""
    except requests.RequestException as exc:
        return None, f"Network error: {exc}"

def search_youtube(query, api_key, order="relevance", max_results=6):
    if not api_key:
        return [], "YouTube Data API key not configured."
    params = {
        "part": "snippet", "q": query, "type": "video", "maxResults": max_results,
        "order": order, "regionCode": "IN", "key": api_key,
    }
    try:
        response = requests.get(YT_SEARCH_URL, params=params, timeout=20)
        data = response.json()
        if response.status_code != 200:
            return [], data.get("error", {}).get("message", f"YouTube API returned HTTP {response.status_code}")
        items = data.get("items", [])
        ids = [item.get("id", {}).get("videoId") for item in items if item.get("id", {}).get("videoId")]
        stats = {}
        if ids:
            stat_response = requests.get(YT_VIDEOS_URL, params={
                "part": "statistics", "id": ",".join(ids), "key": api_key
            }, timeout=20)
            stat_data = stat_response.json()
            if stat_response.status_code == 200:
                stats = {item.get("id"): item.get("statistics", {}) for item in stat_data.get("items", [])}
        results = []
        for item in items:
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            stat = stats.get(video_id, {})
            results.append({
                "title": snippet.get("title", "Untitled"),
                "channel": snippet.get("channelTitle", ""),
                "date": snippet.get("publishedAt", "")[:10],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "views": stat.get("viewCount"),
                "likes": stat.get("likeCount"),
            })
        return results, ""
    except requests.RequestException as exc:
        return [], str(exc)

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def wrap_text(draw, text, fnt, width):
    lines, current = [], ""
    for word in (text or "").split():
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def make_thumbnail(source, headline, label):
    image = source.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)
    image = ImageEnhance.Contrast(image).enhance(1.15)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(1280):
        alpha = int(195 * max(0, 1 - x / 1000))
        od.line((x, 0, x, 720), fill=(0, 0, 0, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(image)
    title_font = get_font(82, True)
    y = 205
    for line in wrap_text(draw, (headline or "EPIC GAMING MOMENT").upper(), title_font, 760)[:3]:
        draw.text((74, y + 5), line, font=title_font, fill=(0, 0, 0, 255), stroke_width=5, stroke_fill=(0, 0, 0, 255))
        draw.text((70, y), line, font=title_font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(20, 20, 20, 255))
        y += 95
    if label.strip():
        draw.rounded_rectangle((70, y + 18, 720, y + 84), radius=16, fill=(255, 190, 25, 245))
        draw.text((90, y + 27), label[:34], font=get_font(38, True), fill=(20, 20, 20, 255))
    return image.convert("RGB")

def ffmpeg_available():
    return shutil.which("ffmpeg") is not None

def process_clip(raw, original_name):
    if not ffmpeg_available():
        return None, "FFmpeg is not available in this environment. For free processing, run KURO locally on a PC after installing FFmpeg."
    ext = Path(original_name).suffix or ".mp4"
    with tempfile.TemporaryDirectory() as td:
        input_path = os.path.join(td, "input" + ext)
        output_path = os.path.join(td, "kuro_export.mp4")
        with open(input_path, "wb") as handle:
            handle.write(raw)
        command = [
            "ffmpeg", "-y", "-i", input_path, "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,eq=contrast=1.04:saturation=1.08",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_path
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=900)
            if result.returncode != 0 or not os.path.exists(output_path):
                return None, "FFmpeg could not process this clip. Try a shorter MP4. " + (result.stderr[-700:] if result.stderr else "")
            with open(output_path, "rb") as handle:
                return handle.read(), ""
        except subprocess.TimeoutExpired:
            return None, "Processing timed out. Try a smaller clip or use your PC locally."

def creator_context():
    return (
        f"Creator brand: KURO. Platform: {st.session_state.get('platform','PS5')}. "
        f"Editing device: {st.session_state.get('device','Both mobile and PC')}. "
        f"Mobile editor: {st.session_state.get('mobile_editor','VN Video Editor')}. "
        f"PC editor: {st.session_state.get('pc_editor','DaVinci Resolve')}. "
        f"Language: {st.session_state.get('language','Hinglish')}. "
        f"Goal: {st.session_state.get('goal','Views and discovery')}."
    )

gemini_key = get_secret("GEMINI_API_KEY")
youtube_key = get_secret("YOUTUBE_API_KEY")

# Brand header
st.markdown("""
<style>
.kuro-title {font-size: 2.3rem; font-weight: 800; letter-spacing: .22em; margin-bottom: 0;}
.kuro-subtitle {font-size: .85rem; letter-spacing: .12em; opacity: .72; margin-top: .2rem;}
div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.2); padding: .65rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)
st.markdown('<p class="kuro-title">KURO</p><p class="kuro-subtitle">GAMING INTELLIGENCE STUDIO · PHASE 01</p>', unsafe_allow_html=True)
st.write("One place to plan gaming videos, create thumbnails, research public videos, and prepare edits.")
st.divider()

with st.sidebar:
    st.header("Creator profile")
    st.session_state.platform = st.selectbox("Gaming platform", ["PS5", "PC", "Xbox", "Mobile", "Multiple"], key="profile_platform")
    st.session_state.device = st.selectbox("Editing setup", ["Both mobile and PC", "Mobile only", "PC only", "Recommend per project"], key="profile_device")
    st.session_state.mobile_editor = st.selectbox("Mobile editor", ["VN Video Editor", "CapCut (if available)", "KineMaster", "InShot", "Not sure"], key="profile_mobile_editor")
    st.session_state.pc_editor = st.selectbox("PC editor", ["DaVinci Resolve", "Clipchamp", "Adobe Premiere Pro", "Not sure"], key="profile_pc_editor")
    st.session_state.language = st.selectbox("Video language", ["Hinglish", "Hindi", "English", "Gujarati", "Choose each time"], key="profile_language")
    st.session_state.goal = st.selectbox("Main goal", ["Views and discovery", "Funny entertainment", "Cinematic storytelling", "Build loyal audience", "Improve editing"], key="profile_goal")
    st.divider()
    st.caption("Free-first setup")
    st.write("AI brain:", "Key configured" if gemini_key else "Not connected yet")
    st.write("YouTube research:", "Key configured" if youtube_key else "Optional / not connected")
    with st.expander("Connect AI later"):
        st.markdown("Create a key at [Google AI Studio](https://aistudio.google.com/apikey), then open Streamlit app settings → Secrets.")
        st.code('GEMINI_API_KEY = "your_key"\nYOUTUBE_API_KEY = "optional_key"', language="toml")
        st.caption("Never commit keys to GitHub. Free tiers and quotas may change.")

tabs = st.tabs(["◈ KURO Chat", "Research", "Thumbnail Lab", "Clip Processor", "Video Blueprint", "Foundation"])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "research_results" not in st.session_state:
    st.session_state.research_results = []
if "research_context" not in st.session_state:
    st.session_state.research_context = ""
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

with tabs[0]:
    st.subheader("Talk to KURO")
    st.write("Example: “I have GTA V, Ghost of Tsushima and God of War. Which one should I play for a funny cinematic Short?”")
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    user_message = st.chat_input("Tell KURO what you want to create...")
    if user_message:
        st.session_state.pending_prompt = user_message
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        context = creator_context()
        if st.session_state.research_context:
            context += "\n\nPublic research sample:\n" + st.session_state.research_context
        with st.spinner("KURO is planning..."):
            answer, error = ask_kuro(st.session_state.chat_history[-12:], gemini_key, context)
        if error:
            answer = f"**AI connection not ready:** {error}\n\nYou can still use the thumbnail lab and try local clip processing. KURO never pretends it researched something when it didn't."
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()
    if st.button("Clear conversation", key="clear_conversation"):
        st.session_state.chat_history = []
        st.rerun()

with tabs[1]:
    st.subheader("Public YouTube research")
    query = st.text_input("Game or video topic", placeholder="e.g. GTA V funny challenge", key="research_query")
    ordering = st.selectbox("Order results", ["Relevance", "Newest", "Most viewed"], key="research_order")
    if st.button("Search public videos", key="research_button", type="primary"):
        if not query.strip():
            st.warning("Enter a game or video topic.")
        elif not youtube_key:
            st.warning("The direct YouTube API needs a key. Use the search links below without a key.")
        else:
            with st.spinner("Searching public video metadata..."):
                results, error = search_youtube(query.strip(), youtube_key, {"Relevance": "relevance", "Newest": "date", "Most viewed": "viewCount"}[ordering])
            if error:
                st.error(error)
            else:
                st.session_state.research_results = results
                st.session_state.research_context = "\n".join(
                    f"{x['title']} | {x['channel']} | {x['date']} | views={x['views']} | {x['url']}" for x in results
                )
                st.success(f"Loaded {len(results)} public search results.")
    if query.strip():
        st.markdown(f"[Open YouTube search](https://www.youtube.com/results?search_query={quote_plus(query.strip())})")
        st.markdown(f"[Search official game news](https://www.google.com/search?q={quote_plus(query.strip() + ' official publisher news')})")
    for item in st.session_state.research_results:
        with st.container(border=True):
            st.markdown(f"**[{item['title']}]({item['url']})**")
            st.caption(f"{item['channel']} · {item['date']} · views: {item['views'] or 'not available'}")

with tabs[2]:
    st.subheader("Thumbnail Lab")
    st.write("Create a clean 1280 × 720 thumbnail from a gameplay screenshot or a simple locally generated abstract background.")
    source_mode = st.radio("Start with", ["My gameplay screenshot", "Abstract background"], key="thumbnail_source_mode")
    source = None
    if source_mode == "My gameplay screenshot":
        uploaded_image = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg", "webp"], key="thumbnail_screenshot")
        if uploaded_image:
            try:
                source = Image.open(uploaded_image).convert("RGB")
            except Exception as exc:
                st.error(f"Couldn't read that image: {exc}")
    else:
        background_style = st.selectbox("Background mood", ["Dark cinematic", "Neon violet", "Sunset orange", "Sci-fi blue"], key="thumbnail_background_style")
        colors = {"Dark cinematic": "#151c28", "Neon violet": "#21103b", "Sunset orange": "#6a2e1d", "Sci-fi blue": "#102b4b"}
        source = Image.new("RGB", (1280, 720), colors[background_style])
        draw = ImageDraw.Draw(source)
        for i in range(13):
            x = 570 + i * 48
            draw.polygon([(x, 0), (min(x + 300, 1280), 0), (min(x + 60, 1280), 720), (max(0, x - 240), 720)],
                         fill=(25 + i * 3, 35 + i * 3, 65 + i * 5))
        draw.ellipse((820, 80, 1190, 450), fill=(240, 135, 40) if background_style == "Sunset orange" else (45, 125, 245))
        source = source.filter(ImageFilter.GaussianBlur(2))
    headline = st.text_input("Main text", placeholder="I BEAT THE IMPOSSIBLE", key="thumbnail_headline")
    label = st.text_input("Small label (optional)", placeholder="NEW CHALLENGE", key="thumbnail_label")
    if source:
        st.image(source, caption="Source preview", use_container_width=True)
        if st.button("Create thumbnail", key="create_thumbnail", type="primary"):
            final_image = make_thumbnail(source, headline, label)
            buffer = io.BytesIO()
            final_image.save(buffer, format="PNG")
            data = buffer.getvalue()
            st.image(data, caption="KURO thumbnail preview · 1280 × 720", use_container_width=True)
            st.download_button("Download thumbnail PNG", data, "kuro_thumbnail.png", "image/png", use_container_width=True)

with tabs[3]:
    st.subheader("Basic clip processor")
    st.warning("This first phase exports a normalized MP4. It does not yet detect highlights, make intelligent cuts, or synchronize edits to music.")
    clip = st.file_uploader("Upload one gameplay clip", type=["mp4", "mov", "mkv", "webm"], key="clip_upload")
    if st.button("Process clip", key="process_clip_button", type="primary"):
        if not clip:
            st.warning("Upload a clip first.")
        else:
            with st.spinner("Processing clip..."):
                output, error = process_clip(clip.getvalue(), clip.name)
            if error:
                st.error(error)
            else:
                st.success("Your MP4 is ready.")
                st.download_button("Download KURO export", output, "kuro_export.mp4", "video/mp4", use_container_width=True)
    st.markdown("For a free local workflow, install FFmpeg on your PC and run KURO locally. On hosted cloud, FFmpeg may not be available.")

with tabs[4]:
    st.subheader("Build a complete video blueprint")
    game = st.text_input("Exact game name", key="blueprint_game", placeholder="Use the exact name you mean")
    idea = st.text_area("Idea or challenge", key="blueprint_idea", placeholder="What should happen in the video?")
    style = st.selectbox("Video style", ["Cinematic", "Funny", "Challenge", "Storytelling", "Fast action", "Horror", "Tutorial", "Shorts"], key="blueprint_style")
    length = st.selectbox("Target length", ["Under 30 seconds", "30–60 seconds", "3–5 minutes", "8–12 minutes", "15+ minutes"], key="blueprint_length")
    voiceover = st.selectbox("Voice-over", ["Yes", "No", "Maybe"], key="blueprint_voiceover")
    if st.button("Create video blueprint", key="create_blueprint", type="primary"):
        st.session_state.pending_prompt = (
            f"Create a complete video blueprint. Exact game: {game}. Idea: {idea}. Style: {style}. Length: {length}. Voice-over: {voiceover}. "
            f"Creator profile: {creator_context()}. Include hook, timestamped script, capture checklist, editor-specific scene instructions, music search terms and licence checks, "
            "three titles, description, relevant tags, thumbnail concept, CTA, and export checklist. Label any unverified trend assumptions."
        )
        st.rerun()

with tabs[5]:
    st.subheader("KURO Phase 1 — Foundation")
    st.markdown("""
**Mission:** give KURO a useful free foundation before investing in cloud services.

**Works without API keys:** thumbnail design from screenshots, abstract thumbnail backgrounds, direct YouTube search links, official-news search links, video blueprint form (AI response needs a key), and basic clip processing when FFmpeg is available.

**Needs a key:** AI chat uses a Gemini API key. Direct public YouTube API results need a YouTube Data API key. Free access, quotas and terms can change.

**Not included yet:** private YouTube Studio analytics, advanced automatic highlight detection, fully AI-generated game artwork, cloud rendering guarantees, and automatic publishing.

**Security:** never paste keys into source code or GitHub. Later channel analytics must use authorized Google sign-in; never share your Google password.
""")
    st.markdown("- [Create a Gemini API key](https://aistudio.google.com/apikey)")
    st.markdown("- [YouTube Audio Library](https://www.youtube.com/audiolibrary)")
    st.markdown("- [FFmpeg downloads](https://ffmpeg.org/download.html)")
    st.markdown("- [Streamlit Community Cloud](https://share.streamlit.io/)")
    st.caption("Phase 1 build · " + datetime.utcnow().strftime("%Y-%m-%d"))
