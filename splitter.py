import base64
import gc
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitAPIException

# ==========================================
# MAX STUDIO PRO - STEM SPLITTER
# ==========================================

try:
    st.set_page_config(
        page_title="MAX Studio Pro",
        page_icon="🎛️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
except StreamlitAPIException:
    pass

APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = APP_DIR / "MAX_Stem_Output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

venv_scripts = Path(sys.executable).parent
if str(venv_scripts) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(venv_scripts) + os.pathsep + os.environ.get("PATH", "")

query_params = st.query_params
if query_params.get("action") in ("split_another", "refresh"):
    st.session_state["split_done"] = False
    st.session_state["is_splitting"] = False
    st.session_state["stem_files"] = {}
    st.session_state["uploaded_audio_bytes"] = None
    st.session_state["uploaded_audio_name"] = None
    st.query_params.clear()
    gc.collect()
    st.rerun()


def sanitize_filename(filename: str) -> str:
    p = Path(filename)
    stem = re.sub(r"[^\w\-]+", "_", p.stem).strip("_") or "audio_track"
    suffix = re.sub(r"[^\w.]", "", p.suffix.lower()) or ".mp3"
    return f"{stem}{suffix}"


def get_hero_logo_html():
    theme_path = APP_DIR / "theme.png"
    if theme_path.is_file():
        b64_img = base64.b64encode(theme_path.read_bytes()).decode("utf-8")
        return f'<img src="data:image/png;base64,{b64_img}" class="hero-logo-img" alt="MAX Studio Pro">'
    return '<div class="hero-symbol">✂</div>'


# ==========================================
# DESIGN / CSS
# ==========================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

.stApp {
    background:
    radial-gradient(ellipse at 78% 0%, rgba(88,25,170,.25), transparent 38%),
    linear-gradient(135deg,#050510,#0b0920,#050510);
    color: white;
    font-family: Inter, sans-serif;
}

[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

.block-container {
    max-width: 1200px;
    padding-top: 0.6rem !important;
    padding-bottom: 3rem;
}

h1,h2,h3,p,label {
    color: #f7f5ff;
}

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin: 0 0 8px 0;
}

.hero {
    display: flex;
    gap: 14px;
    align-items: center;
    margin: 0;
}

.hero-symbol {
    font-size: 56px;
    color: #a72cff;
    text-shadow: 0 0 22px #8c20ff;
    line-height: 1;
}

.hero-logo-img {
    width: 62px;
    height: 62px;
    object-fit: contain;
    border-radius: 12px;
    filter: drop-shadow(0 0 12px rgba(140, 32, 255, 0.75));
}

.hero-title {
    font-size: clamp(25px,4vw,48px);
    font-weight: 900;
    line-height: 1.05;
}

.hero-title span {
    color: #b33cff;
}

.hero-subtitle {
    font-size: clamp(14px, 2vw, 22px);
    font-weight: 500;
    color: #b33cff;
    line-height: 1.2;
    margin-top: 2px;
    letter-spacing: 0.3px;
}

.top-right-container {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    margin-top: 2px;
}

.online-badge {
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    white-space: nowrap;
    padding-top: 2px;
    margin-bottom: 6px;
    text-align: right;
    display: flex;
    align-items: center;
    gap: 7px;
}

.online-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: radial-gradient(circle, #ff5c77 15%, #e60026 60%, #990019 100%);
    border: 1px solid #ff4d6a;
    box-shadow:
        0 0 6px #ff1a3c,
        0 0 14px #ff002b,
        0 0 26px rgba(255, 0, 43, 0.9),
        0 0 40px rgba(200, 0, 30, 0.7);
    animation: redNeonPulse 1.8s infinite ease-in-out;
}

@keyframes redNeonPulse {
    0%, 100% {
        box-shadow:
            0 0 6px #ff1a3c,
            0 0 14px #ff002b,
            0 0 26px rgba(255, 0, 43, 0.9),
            0 0 40px rgba(200, 0, 30, 0.7);
    }
    50% {
        box-shadow:
            0 0 9px #ff4d6a,
            0 0 20px #ff002b,
            0 0 34px rgba(255, 0, 43, 1),
            0 0 52px rgba(220, 0, 35, 0.85);
    }
}

div[data-testid="stRadio"] input[type="radio"] {
    accent-color: #0066ff !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
    border-color: rgba(0, 128, 255, 0.55) !important;
    background-color: transparent !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child * {
    background-color: transparent !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) > div:first-child {
    background: radial-gradient(circle, #0088ff 15%, #0044cc 70%, #002266 100%) !important;
    border-color: #00aaff !important;
    box-shadow: 0 0 8px #0077ff, 0 0 16px rgba(0, 119, 255, 0.95) !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) > div:first-child > div {
    background-color: #ffffff !important;
    box-shadow: 0 0 6px #00ccff !important;
}

.graphic-link-container {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.graphic-link {
    text-decoration: none !important;
    border-bottom: none !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
}

.split-another-top-text {
    font-size: 9px;
    font-weight: 800;
    color: #00d8ff;
    margin-bottom: 4px;
    letter-spacing: 0.5px;
    text-align: center;
    text-shadow: 0 0 8px rgba(0, 216, 255, 0.7);
}

.graphic-glow-blue {
    position: relative;
    width: 96px;
    height: 66px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(0, 119, 255, 0.35) 0%, rgba(5, 5, 16, 0) 75%);
}

.split-player-card {
    width: 86px;
    height: 48px;
    background: #051329;
    border: 1.5px solid #0077ff;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 12px rgba(0, 136, 255, 0.65);
    position: relative;
    transition: all 0.2s ease;
}

.graphic-link:hover .split-player-card {
    border-color: #00d8ff;
    box-shadow: 0 0 18px rgba(0, 216, 255, 0.9);
    transform: translateY(-1px);
}

.sp-screen {
    width: 70px;
    height: 22px;
    background: #0a2042;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.sp-play-icon {
    color: #00d8ff;
    font-size: 14px;
    font-weight: 900;
}

.sp-label {
    font-size: 8.5px;
    font-weight: 800;
    color: #ffffff;
    margin-top: 2px;
    letter-spacing: 0.2px;
}

.sp-badge-card {
    position: absolute;
    bottom: -4px;
    right: -4px;
    background: #0077ff;
    color: #ffffff;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 900;
    border: 1.5px solid #050510;
}

.upload-box {
    text-align: center;
    border: 2px dashed #9a27ff;
    border-bottom: none;
    border-radius: 18px 18px 0 0;
    padding: 6px 10px 16px;
    background: linear-gradient(135deg,rgba(36,13,69,.72),rgba(10,8,30,.8));
    margin-bottom: 0px;
}

.upload-icon {
    font-size: 20px;
    color: #b84aff;
    line-height: 1;
}

.upload-title {
    font-size: 14px;
    font-weight: 700;
    margin-top: 1px;
    line-height: 1.2;
}

.upload-sub {
    color: #b9aed2;
    font-size: 11px;
    margin-top: 1px;
    margin-bottom: 2px;
    line-height: 1.2;
}

div[data-testid="stFileUploader"] {
    border: 2px dashed #9a27ff;
    border-top: none;
    border-radius: 0 0 18px 18px;
    background: linear-gradient(135deg,rgba(36,13,69,.72),rgba(10,8,30,.8));
    padding: 0px 14px 10px 14px;
    margin-top: -12px;
}

div[data-testid="stFileUploader"] section {
    background: rgba(16,10,36,.65);
    border: 1px solid rgba(151,67,255,.35);
    border-radius: 12px;
    padding: 6px 10px;
    min-height: unset !important;
}

div[data-testid="stFileUploader"] section small,
div[data-testid="stFileUploaderDropzoneInstructions"] small,
div[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-size: 9px !important;
    line-height: 1.2 !important;
    white-space: normal !important;
}

div[data-testid="stFileUploader"] button {
    background: linear-gradient(110deg,#a900ed,#442bff) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 4px 12px !important;
    white-space: nowrap !important;
}

.section-title {
    font-size: 17px;
    font-weight: 800;
    margin: 12px 0 6px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    background: linear-gradient(145deg, rgba(20,12,42,0.9), rgba(9,8,25,0.98)) !important;
    border: 1px solid rgba(164, 75, 255, 0.4) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,.35) !important;
    padding: 4px 6px !important;
    margin-bottom: 4px !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] > div {
    gap: 0.2rem !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stElementContainer"] {
    margin-bottom: 0px !important;
}

.stem-head {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
}

.stem-icon {
    font-size: 14px;
    line-height: 1;
}

.stem-desc {
    color: #c8bfdc;
    font-size: 9px;
    margin: 1px 0 0 19px;
    line-height: 1.1;
}

div[data-testid="stVerticalBlockBorderWrapper"] audio {
    height: 26px !important;
    margin: 1px 0 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] div.stDownloadButton > button,
div[data-testid="stVerticalBlockBorderWrapper"] div.stButton > button {
    min-height: 24px !important;
    height: 24px !important;
    padding: 0px 8px !important;
    font-size: 10px !important;
    border-radius: 7px !important;
    margin-bottom: 0px !important;
    line-height: 1 !important;
}

.file-strip {
    border: 1px solid rgba(143,105,218,.5);
    border-radius: 14px;
    padding: 10px 14px;
    background: rgba(18,15,43,.8);
    margin: 10px 0;
}

div.stButton > button,
div.stDownloadButton > button {
    width: 100%;
    min-height: 38px;
    border: 0 !important;
    border-radius: 11px !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    background: linear-gradient(110deg,#a900ed,#442bff) !important;
    box-shadow: 0 5px 18px rgba(117,35,255,.28);
    transition: all .18s ease;
    margin-bottom: 4px;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(117,35,255,.55);
    border: 1px solid #d6a2ff !important;
}

.neon-loader-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 18px 0;
    padding: 8px;
}

.outer-orbit-ring {
    width: 92px;
    height: 92px;
    border-radius: 50%;
    border: 1.5px solid rgba(167, 44, 255, 0.55);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 0 14px rgba(140, 32, 255, 0.65), inset 0 0 8px rgba(140, 32, 255, 0.45);
    background: radial-gradient(circle, rgba(28, 10, 56, 0.9) 0%, rgba(8, 5, 20, 0.99) 100%);
}

.neon-ring {
    width: 76px;
    height: 76px;
    border-radius: 50%;
    background: conic-gradient(#b33cff 0deg, #442bff var(--deg), #211042 var(--deg), #211042 360deg);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 14px rgba(179, 60, 255, 0.65), 0 0 12px rgba(68, 43, 255, 0.55);
}

.neon-ring-inner {
    width: 62px;
    height: 62px;
    background-color: #090618;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(179, 60, 255, 0.35);
}

.neon-center-video-box {
    width: 24px;
    height: 16px;
    background: #14082c;
    border: 1px solid #9a27ff;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 6px rgba(154, 39, 255, 0.75);
    position: relative;
    margin-bottom: 2px;
}

.neon-inner-screen {
    width: 18px;
    height: 10px;
    background: #230e4a;
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.neon-play-arrow {
    color: #c56cff;
    font-size: 8px;
    font-weight: 900;
    filter: drop-shadow(0 0 2px #b33cff);
}

.neon-dot-badge {
    position: absolute;
    bottom: 1px;
    right: 1px;
    width: 3px;
    height: 3px;
    background: #00e89a;
    border-radius: 50%;
    box-shadow: 0 0 2px #00e89a;
}

.neon-percent-text {
    font-size: 12px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.loading-title {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
    margin-top: 8px;
    text-align: center;
    letter-spacing: -0.2px;
}

.loading-subtitle {
    font-size: 10px;
    color: #bdb0d9;
    margin-top: 2px;
    text-align: center;
}

@media(max-width:700px) {
    .block-container {
        padding: 0.5rem .8rem 2rem !important;
    }

    .hero {
        gap: 10px;
    }

    .hero-symbol {
        font-size: 40px;
    }

    .hero-logo-img {
        width: 44px;
        height: 44px;
    }

    .hero-title {
        font-size: 24px;
    }

    .hero-subtitle {
        font-size: 14px;
    }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "split_done": False,
    "is_splitting": False,
    "split_mode": "Fast",
    "output_format": "MP3",
    "stem_files": {},
    "uploaded_audio_bytes": None,
    "uploaded_audio_name": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def trigger_split():
    st.session_state["is_splitting"] = True
    st.session_state["split_done"] = False


# ==========================================
# HELPER: RENDER NEON CIRCULAR LOADER
# ==========================================

def render_neon_loader(placeholder, pct, title_text, sub_text):
    deg = int((pct / 100) * 360)
    loader_html = (
        f'<div class="neon-loader-container">'
        f'<div class="outer-orbit-ring">'
        f'<div class="neon-ring" style="--deg: {deg}deg;">'
        f'<div class="neon-ring-inner">'
        f'<div class="neon-center-video-box">'
        f'<div class="neon-inner-screen">'
        f'<div class="neon-play-arrow">✂</div>'
        f'</div>'
        f'<div class="neon-dot-badge"></div>'
        f'</div>'
        f'<div class="neon-percent-text">{pct}%</div>'
        f'</div></div></div>'
        f'<div class="loading-title">{title_text} ({pct}%)</div>'
        f'<div class="loading-subtitle">{sub_text}</div>'
        f'</div>'
    )
    with placeholder.container():
        st.markdown(loader_html, unsafe_allow_html=True)


# ==========================================
# FFMPEG & AUDIO FORMAT CONVERSION
# ==========================================

FORMAT_CONFIG = {
    "MP3": {"ext": "mp3", "mime": "audio/mpeg", "args": ["-codec:a", "libmp3lame", "-b:a", "320k"]},
    "WAV": {"ext": "wav", "mime": "audio/wav", "args": ["-codec:a", "pcm_s24le"]},
    "FLAC": {"ext": "flac", "mime": "audio/flac", "args": ["-codec:a", "flac"]},
    "M4A": {"ext": "m4a", "mime": "audio/mp4", "args": ["-codec:a", "aac", "-b:a", "256k"]},
    "OGG": {"ext": "ogg", "mime": "audio/ogg", "args": ["-codec:a", "libvorbis", "-q:a", "8"]},
}

MIME_BY_EXT = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
}


def get_ffmpeg():
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg and os.path.isfile(ffmpeg):
        return ffmpeg

    try:
        from static_ffmpeg import run
        ffmpeg, _ = run.get_or_fetch_platform_executables_else_raise()
        if ffmpeg and os.path.isfile(ffmpeg):
            return ffmpeg
    except Exception:
        pass

    return None


def encode_pcm_to_mp3_fallback(pcm16_bytes: bytes, sr: int, n_ch: int, mp3_path: Path) -> bool:
    try:
        import lameenc
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(320)
        encoder.set_in_sample_rate(sr)
        encoder.set_channels(n_ch)
        encoder.set_quality(2)
        mp3_data = encoder.encode(pcm16_bytes) + encoder.flush()
        mp3_path.write_bytes(mp3_data)
        return mp3_path.exists()
    except Exception:
        return False


def convert_audio_format(wav_path, out_path, fmt_key):
    wav_p = Path(wav_path)
    out_p = Path(out_path)
    if not wav_p.exists():
        return None

    if fmt_key == "WAV":
        shutil.copy2(wav_p, out_p)
        return str(out_p)

    ffmpeg = get_ffmpeg()
    if ffmpeg:
        cfg = FORMAT_CONFIG.get(fmt_key, FORMAT_CONFIG["MP3"])
        command = [
            ffmpeg, "-y",
            "-i", str(wav_p),
            *cfg["args"],
            str(out_p)
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0 and out_p.exists():
            return str(out_p)

    if fmt_key == "MP3":
        try:
            import wave
            import numpy as np

            with wave.open(str(wav_p), "rb") as wf:
                n_ch = wf.getnchannels()
                sw = wf.getsampwidth()
                sr = wf.getframerate()
                raw = wf.readframes(wf.getnframes())

            if sw == 2:
                pcm16 = raw
            elif sw == 3:
                b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
                val = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
                val = np.where(val >= 0x800000, val - 0x1000000, val)
                pcm16 = (val >> 8).astype(np.int16).tobytes()
            else:
                arr = np.frombuffer(raw, dtype=np.int32)
                pcm16 = (arr >> 16).astype(np.int16).tobytes()

            if encode_pcm_to_mp3_fallback(pcm16, sr, n_ch, out_p):
                return str(out_p)
        except Exception:
            pass

    return str(wav_p)


def make_instrumental(stem_dir, fmt_key):
    drums = stem_dir / "drums.wav"
    bass = stem_dir / "bass.wav"
    other = stem_dir / "other.wav"
    if not all(p.exists() for p in [drums, bass, other]):
        return None

    cfg = FORMAT_CONFIG.get(fmt_key, FORMAT_CONFIG["MP3"])
    target = stem_dir / f"instruments.{cfg['ext']}"

    ffmpeg = get_ffmpeg()
    if ffmpeg:
        command = [
            ffmpeg, "-y",
            "-i", str(drums),
            "-i", str(bass),
            "-i", str(other),
            "-filter_complex",
            "amix=inputs=3:duration=longest:normalize=0",
            *cfg["args"],
            str(target)
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0 and target.exists():
            return str(target)

    try:
        import wave
        import numpy as np

        def _read_wav_float(p):
            with wave.open(str(p), "rb") as wf:
                n_ch = wf.getnchannels()
                sw = wf.getsampwidth()
                sr = wf.getframerate()
                raw = wf.readframes(wf.getnframes())
            if sw == 2:
                arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            elif sw == 3:
                b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
                val = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
                val = np.where(val >= 0x800000, val - 0x1000000, val)
                arr = val.astype(np.float32) / 8388608.0
            else:
                arr = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
            return arr.reshape(-1, n_ch), sr, n_ch

        d_arr, sr, n_ch = _read_wav_float(drums)
        b_arr, _, _ = _read_wav_float(bass)
        o_arr, _, _ = _read_wav_float(other)

        min_len = min(len(d_arr), len(b_arr), len(o_arr))
        mix = np.clip(d_arr[:min_len] + b_arr[:min_len] + o_arr[:min_len], -1.0, 1.0)
        pcm16 = (mix * 32767.0).astype(np.int16)

        if fmt_key == "MP3":
            mp3_target = stem_dir / "instruments.mp3"
            if encode_pcm_to_mp3_fallback(pcm16.tobytes(), sr, n_ch, mp3_target):
                return str(mp3_target)

        wav_target = stem_dir / "instruments.wav"
        with wave.open(str(wav_target), "wb") as wf:
            wf.setnchannels(n_ch)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm16.tobytes())

        if fmt_key != "WAV":
            converted = convert_audio_format(wav_target, target, fmt_key)
            if converted and Path(converted).exists():
                return converted

        if wav_target.exists():
            return str(wav_target)
    except Exception:
        pass

    return None


# ==========================================
# DEMUCS STEM SPLITTER (TURBO FAST + LOW-RAM SAFE)
# ==========================================

def run_demucs(audio_bytes, audio_name, model_name, shifts, overlap, out_fmt, progress_placeholder):
    gc.collect()

    render_neon_loader(
        progress_placeholder,
        1,
        "Preparing AI Engine...",
        "Please do not close the app"
    )

    safe_name = sanitize_filename(audio_name)
    input_path = OUTPUT_DIR / safe_name
    input_path.write_bytes(audio_bytes)

    device = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
    except Exception:
        pass

    cpu_threads = str(min(4, max(1, os.cpu_count() or 2)))
    segment_len = "7"

    wrapper_code = (
        "import os, sys, gc\n"
        f"os.environ['OMP_NUM_THREADS'] = '{cpu_threads}'\n"
        f"os.environ['MKL_NUM_THREADS'] = '{cpu_threads}'\n"
        "try:\n"
        "    import torch\n"
        f"    torch.set_num_threads({cpu_threads})\n"
        "except Exception:\n"
        "    pass\n"
        "try:\n"
        "    import torchaudio, soundfile as sf\n"
        "    def _sf_save(uri, src, sample_rate, **kwargs):\n"
        "        data = src.detach().cpu().numpy()\n"
        "        if data.ndim == 2:\n"
        "            data = data.T\n"
        "        sf.write(str(uri), data, sample_rate, subtype='PCM_24')\n"
        "    torchaudio.save = _sf_save\n"
        "except Exception:\n"
        "    pass\n"
        "from demucs.separate import main\n"
        "rc = main()\n"
        "gc.collect()\n"
        "sys.exit(rc)\n"
    )

    command = [
        sys.executable, "-u", "-c", wrapper_code,
        "-n", model_name,
        "--device", device,
        "--int24",
        "-j", "1",
        "--shifts", str(shifts),
        "--segment", segment_len,
        "--overlap", str(overlap),
        "-o", str(OUTPUT_DIR),
        str(input_path)
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["OMP_NUM_THREADS"] = cpu_threads
    env["MKL_NUM_THREADS"] = cpu_threads

    logs = []
    current_pct = 1

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env=env
        )

        buffer = ""
        while True:
            chunk = process.stdout.read(64)
            if not chunk and process.poll() is not None:
                break
            if chunk:
                text_chunk = chunk.decode("utf-8", errors="ignore")
                buffer += text_chunk
                logs.append(text_chunk)
                if len(logs) > 250:
                    logs = logs[-150:]

                matches = re.findall(r"(\d{1,3})%\|", buffer)
                if matches:
                    pct = min(int(matches[-1]), 95)
                    if pct > current_pct:
                        current_pct = pct
                        render_neon_loader(
                            progress_placeholder,
                            current_pct,
                            "Separating Audio...",
                            f"Device: {device.upper()} • Turbo Fast Engine"
                        )
                    buffer = buffer[-100:]

        returncode = process.wait()

    except Exception as e:
        progress_placeholder.empty()
        st.error(f"Failed to start Demucs: {e}")
        return None

    full_log = "".join(logs)

    if returncode != 0:
        progress_placeholder.empty()
        st.error("Stem separation failed (Memory/Engine error):")
        st.code(full_log[-4000:] if full_log else "Process killed (Out of Memory). Audio tawi zawk hmang chhin rawh.")
        gc.collect()
        return None

    render_neon_loader(
        progress_placeholder,
        98,
        f"Converting to {out_fmt}...",
        "Almost done, please wait"
    )

    song_folder = OUTPUT_DIR / model_name / Path(safe_name).stem

    expected = {
        "Vocals": song_folder / "vocals.wav",
        "Drum": song_folder / "drums.wav",
        "Bass": song_folder / "bass.wav",
        "Other": song_folder / "other.wav",
    }

    missing = [name for name, path in expected.items() if not path.exists()]
    if missing:
        progress_placeholder.empty()
        st.error("Missing stems: " + ", ".join(missing))
        if full_log:
            st.code(full_log[-3000:])
        return None

    ext = FORMAT_CONFIG.get(out_fmt, FORMAT_CONFIG["MP3"])["ext"]

    converted_outputs = {}
    for name, wav_path in expected.items():
        out_path = song_folder / f"{name.lower()}_out.{ext}"
        converted_outputs[name] = convert_audio_format(wav_path, out_path, out_fmt)

    instrumental_path = make_instrumental(song_folder, out_fmt)
    converted_outputs["Instruments"] = str(instrumental_path) if instrumental_path else None

    render_neon_loader(
        progress_placeholder,
        100,
        "Completed!",
        "Your separated tracks are ready"
    )
    progress_placeholder.empty()
    gc.collect()

    return converted_outputs


# ==========================================
# STEM RESULT CARDS (ULTRA-COMPACT)
# ==========================================

def stem_card(name, icon, desc, color):
    path = st.session_state["stem_files"].get(name)

    with st.container(border=True):
        st.markdown(
            f'<div style="border-left: 3px solid {color}; padding-left: 6px; margin-bottom: 1px;">'
            f'<div class="stem-head"><span class="stem-icon">{icon}</span><span style="color: white;">{name}</span></div>'
            f'<div class="stem-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if path and Path(path).is_file():
            file_p = Path(path)
            ext = file_p.suffix.lstrip(".").lower() or "mp3"
            mime = MIME_BY_EXT.get(ext, "audio/wav")
            audio_bytes = file_p.read_bytes()

            st.audio(audio_bytes, format=mime)

            st.download_button(
                f"⬇ Download {name} (.{ext})",
                data=audio_bytes,
                file_name=f"{name.lower()}.{ext}",
                mime=mime,
                key=f"download_{name}",
                use_container_width=True
            )
        else:
            st.button(
                f"Unavailable ({name})",
                key=f"disabled_{name}",
                disabled=True,
                use_container_width=True
            )


# ==========================================
# MAIN INTERFACE (STEM SPLITTER)
# ==========================================

if st.session_state["split_done"]:
    top_right_card_html = '<div class="graphic-link-container"><a href="?action=split_another" target="_self" class="graphic-link" title="Split Another Audio"><div class="split-another-top-text">SPLIT ANOTHER</div><div class="graphic-glow-blue"><div class="split-player-card"><div class="sp-screen"><span class="sp-play-icon">✂</span></div><div class="sp-label">New Audio</div><div class="sp-badge-card">↻</div></div></div></a></div>'
else:
    top_right_card_html = '<div class="graphic-link-container"><a href="?action=refresh" target="_self" class="graphic-link" title="Refresh App"><div class="split-another-top-text">REFRESH</div><div class="graphic-glow-blue"><div class="split-player-card"><div class="sp-screen"><span class="sp-play-icon">↻</span></div><div class="sp-label">Reload App</div><div class="sp-badge-card">↻</div></div></div></a></div>'

hero_logo_html = get_hero_logo_html()
top_bar_html = f'<div class="top-bar"><div class="hero">{hero_logo_html}<div><div class="hero-title">MAX STUDIO <span>PRO</span></div><div class="hero-subtitle">Stem Splitter</div></div></div><div class="top-right-container"><div class="online-badge"><span class="online-dot"></span> Online</div>{top_right_card_html}</div></div>'

st.markdown(top_bar_html, unsafe_allow_html=True)

if not st.session_state["split_done"]:
    st.markdown(
        '<div class="upload-box"><div class="upload-icon">☁️ ↑</div><div class="upload-title">Add Your Audio File</div><div class="upload-sub">Choose an audio file below to begin</div></div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Select audio file",
        type=["mp3", "wav", "flac", "m4a", "ogg", "aiff", "aif"],
        label_visibility="collapsed",
        key="audio_upload"
    )

    file_ready = False
    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        if raw_bytes and len(raw_bytes) == uploaded_file.size and uploaded_file.size > 0:
            st.session_state["uploaded_audio_bytes"] = raw_bytes
            st.session_state["uploaded_audio_name"] = uploaded_file.name
            file_ready = True
    else:
        st.session_state["uploaded_audio_bytes"] = None
        st.session_state["uploaded_audio_name"] = None

    if file_ready:
        ext = Path(st.session_state["uploaded_audio_name"]).suffix.replace(".", "").upper()
        if ext == "AIF":
            ext = "AIFF"

        file_size_mb = len(st.session_state["uploaded_audio_bytes"]) / (1024 * 1024)
        safe_display_name = html.escape(st.session_state["uploaded_audio_name"])

        st.markdown(
            f'<div class="file-strip">🎵 <b>Selected File:</b> {safe_display_name} | {file_size_mb:.2f} MB | ✓ Format: <b>{ext}</b></div>',
            unsafe_allow_html=True
        )
        st.audio(st.session_state["uploaded_audio_bytes"])

    controls_placeholder = st.empty()

    if not st.session_state["is_splitting"]:
        with controls_placeholder.container():
            st.markdown('<div class="section-title">⚙️ Splitting Quality</div>', unsafe_allow_html=True)
            st.radio("Choose splitting quality", ["Fast", "Normal", "HQ"], key="split_mode", horizontal=True)

            st.markdown('<div class="section-title">🎧 Output Format</div>', unsafe_allow_html=True)
            st.radio("Choose output audio format", ["MP3", "WAV", "FLAC", "M4A", "OGG"], key="output_format", horizontal=True)

            if file_ready:
                st.button("▶ START SPLITTING", key="start_splitting", on_click=trigger_split, use_container_width=True)

    if st.session_state["is_splitting"]:
        st.session_state["is_splitting"] = False
        if file_ready:
            selected_mode = st.session_state["split_mode"]
            selected_fmt = st.session_state["output_format"]

            if selected_mode == "Fast":
                model_name = "htdemucs"
                shifts = 0
                overlap = 0.05
            elif selected_mode == "Normal":
                model_name = "htdemucs"
                shifts = 0
                overlap = 0.1
            else:
                model_name = "htdemucs"
                shifts = 1
                overlap = 0.2

            outputs = run_demucs(
                st.session_state["uploaded_audio_bytes"],
                st.session_state["uploaded_audio_name"],
                model_name,
                shifts,
                overlap,
                selected_fmt,
                controls_placeholder
            )

            if outputs:
                st.session_state["stem_files"] = dict(outputs)
                st.session_state["split_done"] = True
                gc.collect()
                st.rerun()

# ======================================
# STEM RESULTS
# ======================================

if st.session_state["split_done"]:
    st.markdown('<div class="section-title">🎚️ STEM RESULTS</div>', unsafe_allow_html=True)

    cards = [
        ("Vocals", "🎙️", "Isolated vocal track", "#ff28b8"),
        ("Drum", "🥁", "Drum and percussion track", "#168dff"),
        ("Bass", "🎸", "Bass line", "#00df83"),
        ("Other", "💿", "Melody track (without vocals, drum, or bass)", "#ff8a19"),
        ("Instruments", "🎹", "Combined instrumental mix", "#00d9ee"),
    ]

    for name, icon, desc, color in cards:
        stem_card(name, icon, desc, color)