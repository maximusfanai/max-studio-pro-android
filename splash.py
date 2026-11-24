import base64
import os
import time
import streamlit as st
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="MAX Studio Pro",
    page_icon="🎛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Base directory setting (Linux & Windows compatible)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Function to encode local image to Base64 with E:\MaxStudioPro priority & fallback
def get_image_base64(filename, preferred_dir=r"E:\MaxStudioPro"):
  search_dirs = [preferred_dir, BASE_DIR]
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


# Paths loading from E:\MaxStudioPro first, then BASE_DIR
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

# --- 1. SPLASH SCREEN ---
if st.session_state["show_splash"]:
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
      f'<div class="transparent-bg-layer"><img src="{logo_b64}" class="transparent-bg-img" /></div>'
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
        </style>
        {bg_watermark_html}
        """,
      unsafe_allow_html=True,
  )

  if theme_img_b64:
    st.markdown(
        f"<div style='text-align: center; margin-top: 0px; margin-bottom:"
        f" 0px; position: relative; z-index: 2;'><img src='{theme_img_b64}' style='width: 70px; height:"
        " auto;' /></div>",
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
    email_input = st.text_input(
        "Email or phone", placeholder="Enter your Gmail..."
    )
    pass_input = st.text_input(
        "Password", type="password", placeholder="Enter password..."
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign in with Google", use_container_width=True, type="primary"):
      if email_input.strip() != "" and pass_input.strip() != "":
        st.session_state["logged_in"] = True
        st.success("Google Authentication Successful!")
        time.sleep(1)
        st.rerun()
      else:
        st.warning("Please enter both email and password to continue.")

    if st.button("Back", use_container_width=True):
      st.session_state["show_google_auth"] = False
      st.rerun()

# --- 3. WELCOME SCREEN ---
else:
  bg_watermark_html = (
      f'<div class="transparent-bg-layer"><img src="{logo_b64}" class="transparent-bg-img" /></div>'
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
          f"<div style='text-align: center; margin-top: 100px;"
          f" margin-bottom: 0px; position: relative; z-index: 2;'><img src='{theme_img_b64}' style='width:"
          " 110px; height: auto;' /></div>",
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