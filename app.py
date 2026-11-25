import base64
import importlib.util
import os
from pathlib import Path
import time
from urllib.parse import urlencode

import requests
import streamlit as st
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="MAX Studio Pro",
    page_icon="🎛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ==========================================
# GOOGLE OAUTH SETTINGS (Localhost & Cloud Auto-Detect)
# ==========================================
def get_secret(key: str, default: str = "") -> str:
  try:
    if key in st.secrets:
      return str(st.secrets[key]).strip()
  except Exception:
    pass
  return os.environ.get(key, default).strip()


def resolve_redirect_uri() -> str:
  """Localhost a nih chuan http://localhost:<port>, Cloud a nih chuan live URL a pe chhuak."""
  try:
    headers = getattr(st.context, "headers", {}) or {}
    host = headers.get("Host") or headers.get("host") or ""
    if host:
      if host.startswith("localhost") or host.startswith("127.0.0.1"):
        return f"http://{host}"
      return f"https://{host}"
  except Exception:
    pass

  configured = get_secret("REDIRECT_URI", "") or get_secret(
      "GOOGLE_REDIRECT_URI", ""
  )
  if configured:
    return configured.rstrip("/")

  port = st.get_option("server.port") or 8504
  return f"http://localhost:{port}"


GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = resolve_redirect_uri()

AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

# ==========================================
# PATHS & SPLITTER CONFIG
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPLITTER_PATH = Path(BASE_DIR) / "splitter.py"
if not SPLITTER_PATH.exists():
  SPLITTER_PATH = Path(r"E:\MaxStudioPro\splitter.py")


def get_image_base64(filename, preferred_dir=r"E:\MaxStudioPro"):
  search_dirs = [BASE_DIR, preferred_dir]
  for d in search_dirs:
    if not d or not os.path.exists(d):
      continue
    target_path = os.path.join(d, filename)
    if not os.path.exists(target_path):
      base_name = filename.lower()
      for f in os.listdir(d):
        if f.lower() == base_name:
          target_path = os.path.join(d, f)
          break

    if os.path.exists(target_path):
      with open(target_path, "rb") as f:
        data = f.read()
      return f"data:image/png;base64,{base64.b64encode(data).decode()}"
  return ""


def run_splitter_module():
  """splitter.py hi Google Sign-In zawh hnuah a run nghal."""
  if not SPLITTER_PATH.exists():
    st.error(f"splitter.py file hmuh a ni lo: {SPLITTER_PATH}")
    st.info("Repository root-ah splitter.py file dah lut rawh.")
    return

  orig_set_page_config = st.set_page_config

  def _safe_set_page_config(*args, **kwargs):
    try:
      return orig_set_page_config(*args, **kwargs)
    except Exception:
      return None

  st.set_page_config = _safe_set_page_config
  try:
    spec = importlib.util.spec_from_file_location(
        "max_splitter", str(SPLITTER_PATH)
    )
    if spec and spec.loader:
      splitter_mod = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(splitter_mod)
      for fn_name in ("main", "render_splitter", "run_app", "run"):
        fn = getattr(splitter_mod, fn_name, None)
        if callable(fn):
          fn()
          break
  except Exception as e:
    st.error(f"splitter.py run laiin error a awm: {e}")
  finally:
    st.set_page_config = orig_set_page_config


logo_b64 = get_image_base64("logo.png", r"E:\MaxStudioPro")
theme_img_b64 = get_image_base64("theme.png", r"E:\MaxStudioPro")

# Session state initialization
if "show_splash" not in st.session_state:
  st.session_state["show_splash"] = True

if "show_login" not in st.session_state:
  st.session_state["show_login"] = False

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

if "show_google_auth" not in st.session_state:
  st.session_state["show_google_auth"] = False

if "login_page_loaded_time" not in st.session_state:
  st.session_state["login_page_loaded_time"] = None

if "user_name" not in st.session_state:
  st.session_state["user_name"] = ""

if "user_email" not in st.session_state:
  st.session_state["user_email"] = ""


# ==========================================
# GOOGLE OAUTH CALLBACK HANDLER
# ==========================================
def handle_google_oauth_callback():
  code = st.query_params.get("code")
  if code and not st.session_state["logged_in"]:
    try:
      token_resp = requests.post(
          TOKEN_ENDPOINT,
          data={
              "code": code,
              "client_id": GOOGLE_CLIENT_ID,
              "client_secret": GOOGLE_CLIENT_SECRET,
              "redirect_uri": REDIRECT_URI,
              "grant_type": "authorization_code",
          },
          timeout=10,
      )
      token_json = token_resp.json()
      access_token = token_json.get("access_token")
      if access_token:
        user_resp = requests.get(
            USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        user_info = user_resp.json()
        st.session_state["logged_in"] = True
        st.session_state["show_splash"] = False
        st.session_state["show_google_auth"] = False
        st.session_state["user_email"] = user_info.get("email", "")
        st.session_state["user_name"] = user_info.get("name", "User")
        st.query_params.clear()
        st.rerun()
      else:
        st.session_state["show_splash"] = False
        st.session_state["show_google_auth"] = True
        st.error(
            "Google Login failed:"
            f" {token_json.get('error_description', token_json)}"
        )
    except Exception as e:
      st.session_state["show_splash"] = False
      st.session_state["show_google_auth"] = True
      st.error(f"Google Sign-In error: {e}")


handle_google_oauth_callback()


# ==========================================
# LOGGED IN -> LAUNCH splitter.py
# ==========================================
if st.session_state["logged_in"]:
  with st.sidebar:
    st.markdown("### MAX Studio Pro")
    if st.session_state["user_email"]:
      st.caption(
          f"{st.session_state['user_name']} ({st.session_state['user_email']})"
      )
    if st.button("Sign Out", use_container_width=True):
      st.session_state["logged_in"] = False
      st.session_state["show_google_auth"] = True
      st.session_state["user_name"] = ""
      st.session_state["user_email"] = ""
      st.rerun()

  run_splitter_module()

# --- 1. SPLASH SCREEN ---
elif st.session_state["show_splash"]:
  st.markdown(
      f"""
        <style>
            .stApp {{
                background: #06060e !important;
                overflow: hidden !important;
            }}
            html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"], .main, .block-container {{
                background-color: #06060e !important;
                margin: 0 !important;
                padding: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                overflow: hidden !important;
            }}
            .main .block-container {{
                padding: 0 !important;
                max-width: 100% !important;
                height: 100vh !important;
                display: flex !important;
                align-items: flex-start !important;
                justify-content: center !important;
                overflow: hidden !important;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
            .splash-container {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                display: flex;
                align-items: flex-start;
                justify-content: center;
                background: #06060e;
                margin: 0;
                padding: 0;
                animation: fadeIn 3.0s ease-in-out;
                overflow: hidden !important;
            }}
            .splash-logo-img {{
                width: 100vw;
                height: 100vh;
                object-fit: cover;
                object-position: top center;
                display: block;
                margin: 0;
                padding: 0;
            }}
            #MainMenu, footer, header {{visibility: hidden;}}
        </style>

        <div class="splash-container">
            {"<img src='" + logo_b64 + "' class='splash-logo-img' />" if logo_b64 else ""}
        </div>
        """,
      unsafe_allow_html=True,
  )

  components.html(
      """
        <script>
            setTimeout(function() {
                window.parent.document.querySelector('iframe').contentWindow.location.reload();
            }, 6000);
        </script>
        """,
      height=0,
      width=0,
  )

  time.sleep(6.0)
  st.session_state["show_splash"] = False
  st.session_state["login_page_loaded_time"] = time.time()
  st.rerun()

# --- 2. GOOGLE AUTH LOGIN SCREEN ---
elif st.session_state["show_google_auth"]:
  bg_watermark_html = (
      '<div class="transparent-bg-layer"><img'
      f' src="{logo_b64}" class="transparent-bg-img" /></div>'
      if logo_b64
      else ""
  )

  st.markdown(
      f"""
        <style>
            html, body, .stApp {{
                background: #06060e !important;
                color: white !important;
                overflow: hidden !important;
                height: 100vh !important;
                max-height: 100vh !important;
            }}
            [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"], .main, .block-container {{
                background: transparent !important;
                overflow: hidden !important;
                height: 100vh !important;
                max-height: 100vh !important;
                position: relative;
                z-index: 2;
            }}
            .transparent-bg-layer {{
                position: fixed;
                inset: 0;
                width: 100vw;
                height: 100vh;
                z-index: 0;
                pointer-events: none;
                overflow: hidden;
            }}
            .transparent-bg-img {{
                width: 100vw;
                height: 100vh;
                object-fit: cover;
                object-position: top center;
                opacity: 0.14;
                display: block;
            }}
            #MainMenu, footer, header {{visibility: hidden;}}
            .google-logo {{
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 5px;
                letter-spacing: -1px;
                text-align: center;
                position: relative;
                z-index: 2;
            }}
            .g-blue {{ color: #4285F4; }}
            .g-red {{ color: #EA4335; }}
            .g-yellow {{ color: #FBBC05; }}
            .g-green {{ color: #34A853; }}
            .login-title {{
                text-align: center;
                margin-top: 5px;
                margin-bottom: 5px;
                font-size: 26px;
                font-weight: 900;
                letter-spacing: 0.5px;
                background: linear-gradient(135deg, #ffffff 0%, #d8b4fe 35%, #b33cff 68%, #00d8ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                filter: drop-shadow(0 0 10px rgba(179, 60, 255, 0.45));
                position: relative;
                z-index: 2;
            }}
            .google-oauth-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                width: 100%;
                padding: 12px 16px;
                border-radius: 10px;
                background: linear-gradient(110deg, #b300ff 0%, #5b2bff 52%, #0099ff 100%);
                color: #ffffff !important;
                font-weight: 800;
                font-size: 15px;
                text-decoration: none !important;
                border: 1px solid rgba(0, 216, 255, 0.45);
                box-shadow: 0 0 18px rgba(179, 0, 255, 0.55), 0 0 28px rgba(0, 153, 255, 0.35);
                margin-top: 12px;
                margin-bottom: 12px;
                transition: all 0.2s ease;
            }}
            .google-oauth-btn:hover {{
                transform: scale(1.03);
                border-color: #00d8ff;
                box-shadow: 0 0 24px rgba(179, 0, 255, 0.8), 0 0 36px rgba(0, 216, 255, 0.65);
            }}
            .stButton>button {{
                background: linear-gradient(110deg, #b300ff 0%, #5b2bff 52%, #0099ff 100%) !important;
                color: #ffffff !important;
                border: 1px solid rgba(0, 216, 255, 0.45) !important;
                border-radius: 10px !important;
                font-weight: 800 !important;
                letter-spacing: 0.4px;
                box-shadow: 0 0 18px rgba(179, 0, 255, 0.5), 0 0 28px rgba(0, 153, 255, 0.35) !important;
                transition: all 0.2s ease !important;
            }}
            .stButton>button:hover {{
                transform: scale(1.04);
                border-color: #00d8ff !important;
                box-shadow: 0 0 24px rgba(179, 0, 255, 0.8), 0 0 36px rgba(0, 216, 255, 0.65) !important;
                color: #ffffff !important;
            }}
        </style>
        {bg_watermark_html}
        """,
      unsafe_allow_html=True,
  )

  if theme_img_b64:
    st.markdown(
        "<div style='text-align: center; margin-top: 0px; margin-bottom:"
        f" 0px; position: relative; z-index: 2;'><img src='{theme_img_b64}'"
        " style='width: 70px; height: auto;' /></div>",
        unsafe_allow_html=True,
    )

  st.markdown(
      '<div class="login-title">MAX Studio Pro</div>', unsafe_allow_html=True
  )

  st.markdown(
      """
        <div class="google-logo" style="margin-top: 0px; margin-bottom: 5px;">
            <span class="g-blue">G</span><span class="g-red">o</span><span class="g-yellow">o</span><span class="g-blue">g</span><span class="g-green">l</span><span class="g-red">e</span>
        </div>
        """,
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
      st.warning(
          "Secrets-ah GOOGLE_CLIENT_ID leh GOOGLE_CLIENT_SECRET dah lut rawh."
      )
    else:
      params = urlencode({
          "client_id": GOOGLE_CLIENT_ID,
          "redirect_uri": REDIRECT_URI,
          "response_type": "code",
          "scope": "openid email profile",
          "access_type": "offline",
          "prompt": "select_account",
      })
      google_auth_url = f"{AUTHORIZE_ENDPOINT}?{params}"
      st.markdown(
          f'<a href="{google_auth_url}" target="_blank" rel="noopener'
          ' noreferrer" class="google-oauth-btn">Sign in with Google</a>',
          unsafe_allow_html=True,
      )

    if st.button("Back", use_container_width=True):
      st.session_state["show_google_auth"] = False
      st.rerun()

# --- 3. WELCOME SCREEN ---
else:
  bg_watermark_html = (
      '<div class="transparent-bg-layer"><img'
      f' src="{logo_b64}" class="transparent-bg-img" /></div>'
      if logo_b64
      else ""
  )

  st.markdown(
      f"""
        <style>
            html, body, .stApp {{
                background: #06060e !important;
                color: white !important;
                overflow: hidden !important;
                height: 100vh !important;
                max-height: 100vh !important;
            }}
            [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"], .main, .block-container {{
                background: transparent !important;
                overflow: hidden !important;
                height: 100vh !important;
                max-height: 100vh !important;
                padding-top: 5px !important;
                position: relative;
                z-index: 2;
            }}
            .transparent-bg-layer {{
                position: fixed;
                inset: 0;
                width: 100vw;
                height: 100vh;
                z-index: 0;
                pointer-events: none;
                overflow: hidden;
            }}
            .transparent-bg-img {{
                width: 100vw;
                height: 100vh;
                object-fit: cover;
                object-position: top center;
                opacity: 0.14;
                display: block;
            }}
            #MainMenu, footer, header {{visibility: hidden;}}
            .login-container {{
                margin-top: 180px;
                text-align: center;
                width: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .login-title {{
                text-align: center;
                margin-top: 12px;
                margin-bottom: 18px;
                font-size: 32px;
                font-weight: 900;
                letter-spacing: 0.5px;
                background: linear-gradient(135deg, #ffffff 0%, #d8b4fe 35%, #b33cff 68%, #00d8ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                filter: drop-shadow(0 0 14px rgba(179, 60, 255, 0.55));
                position: relative;
                z-index: 2;
            }}
            @keyframes popUp {{
                0% {{ opacity: 0; transform: scale(0.8); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}
            .welcome-btn-wrapper {{
                animation: popUp 0.5s ease-out forwards;
                width: 100%;
                position: relative;
                z-index: 2;
            }}
            .stButton>button {{
                background: linear-gradient(110deg, #b300ff 0%, #5b2bff 52%, #0099ff 100%) !important;
                color: #ffffff !important;
                border: 1px solid rgba(0, 216, 255, 0.45) !important;
                border-radius: 10px !important;
                font-weight: 800 !important;
                letter-spacing: 0.4px;
                box-shadow: 0 0 18px rgba(179, 0, 255, 0.5), 0 0 28px rgba(0, 153, 255, 0.35) !important;
                transition: all 0.2s ease !important;
            }}
            .stButton>button:hover {{
                transform: scale(1.04);
                border-color: #00d8ff !important;
                box-shadow: 0 0 24px rgba(179, 0, 255, 0.8), 0 0 36px rgba(0, 216, 255, 0.65) !important;
                color: #ffffff !important;
            }}
        </style>
        {bg_watermark_html}
        """,
      unsafe_allow_html=True,
  )

  delay_seconds = 1.0
  elapsed_time = (
      time.time() - st.session_state["login_page_loaded_time"]
      if st.session_state["login_page_loaded_time"]
      else 0
  )

  if elapsed_time < delay_seconds:
    time.sleep(delay_seconds - elapsed_time)
    st.rerun()
  else:
    if theme_img_b64:
      st.markdown(
          "<div style='text-align: center; margin-top: 100px;"
          " margin-bottom: 0px; position: relative; z-index: 2;'><img"
          f" src='{theme_img_b64}' style='width: 110px; height: auto;' /></div>",
          unsafe_allow_html=True,
      )

    st.markdown(
        '<div class="login-title">MAX Studio Pro</div>', unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([2.0, 4.0, 2.0])
    with col2:
      st.markdown('<div class="welcome-btn-wrapper">', unsafe_allow_html=True)
      if st.button("Welcome", use_container_width=True, type="primary"):
        st.session_state["show_google_auth"] = True
        st.rerun()

      st.markdown("</div>", unsafe_allow_html=True)
