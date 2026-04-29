import streamlit as st
import os
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURACIÓN (ESTA DEBE SER LA PRIMERA LÍNEA DE STREAMLIT) ---
st.set_page_config(page_title="English Practice Portal", layout="centered", page_icon="🇬🇧")

# --- 2. CSS PARA OCULTAR INTERFAZ ---
# Aquí corregí el error: usamos 'unsafe_allow_html=True' que es el correcto.
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    .reading-box {
        background-color: #f8f9fa; padding: 25px; border-radius: 15px;
        border-left: 8px solid #1E88E5; font-size: 1.1rem; line-height: 1.6;
        color: #1a1a1a; margin-bottom: 20px;
    }
    .stButton button { width: 100%; border-radius: 10px; font-weight: bold; }
    .teacher-tip { 
        background-color: #fff3cd; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #ffc107; margin: 10px 0;
    }
    .pos { color: #2e7d32; font-weight: bold; }
    .neg { color: #c62828; font-weight: bold; }
    .int { color: #1565c0; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNCIONES ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CLASES_DIR = os.path.join(BASE_PATH, "Clases")
USERS = {"alumna": "password2026", "profe": "admin123"}

def display_logo(lec_sel=None):
    path = os.path.join(CLASES_DIR, "Leccion_01", "logo.png")
    if lec_sel:
        alt_path = os.path.join(CLASES_DIR, lec_sel, "logo.png")
        if os.path.exists(alt_path): path = alt_path
    if os.path.exists(path):
        _, col, _ = st.columns([1, 1, 1])
        with col: st.image(path, width=220)

def text_to_speech(text):
    try:
        clean = text.split('(')[0].replace('_', '').strip()
        tts = gTTS(text=clean, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- 4. LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    display_logo()
    st.markdown("<h2 style='text-align:center;'>🔐 Private Access</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if u in USERS and USERS[u] == p:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else: st.error("❌ Invalid credentials")
    st.stop()

# --- 5. CONTENIDO PRINCIPAL ---
if st.session_state["authenticated"]:
    with st.sidebar:
        st.title("Navigation")
        if os.path.exists(CLASES_DIR):
            lecciones = sorted([d for d in os.listdir(CLASES_DIR) if os.path.isdir(os.path.join(CLASES_DIR, d))])
        else:
            lecciones = []
        
        lec_sel = st.selectbox("Select Lesson:", lecciones) if lecciones else None
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    if lec_sel:
        display_logo(lec_sel)
        txt_path = os.path.join(CLASES_DIR, lec_sel, "material.txt")
        
        # Procesamiento de archivo material.txt (Igual que antes)
        content = {"theory": [], "speaking": [], "reading": []}
        FORBIDDEN_TAGS = ["GRAMMAR", "EXERCISES", "COMPLETE", "TRANSLATE", "READING", "THEORY"]
        
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            
            curr_section = "general"
            for l in lines:
                if l.startswith("[THEORY:"):
                    curr_section = "theory"
                    content["theory"].append({"title": l[8:-1], "data": {}, "exercises": []})
                elif l.startswith("[READING:"):
                    curr_section = "reading"
                    content["reading"].append({"title": l[9:-1], "text": []})
                elif l.startswith("["):
                    section_name = l[1:-1]
                    if not any(tag in section_name.upper() for tag in FORBIDDEN_TAGS):
                        curr_section = "speaking"
                        content["speaking"].append({"title": section_name, "items": []})
                    else:
                        curr_section = "exercises"
                else:
                    if curr_section == "theory":
                        tag = l.split(":")[0] if ":" in l else "TEXT"
                        val = l.split(":", 1)[1].strip() if ":" in l else l
                        if tag not in content["theory"][-1]["data"]: content["theory"][-1]["data"][tag] = []
                        content["theory"][-1]["data"][tag].append(val)
                    elif curr_section == "speaking":
                        content["speaking"][-1]["items"].append(l)
                    elif curr_section == "reading":
                        content["reading"][-1]["text"].append(l)

        # --- TABS ---
        t1, t2, t3 = st.tabs(["📚 Theory", "🎤 Speaking", "✍️ Writing"])
        
        with t1:
            if content["theory"]:
                for t in content["theory"]:
                    st.subheader(t["title"])
                    if "CONCEPTO" in t["data"]: st.write(t["data"]["CONCEPTO"][0])
            else: st.info("Select a lesson to start.")

        with t2:
            if content["speaking"]:
                for s in content["speaking"]:
                    st.write(f"### {s['title']}")
                    for item in s["items"]:
                        c1, c2 = st.columns([3, 1])
                        c1.write(item)
                        with c2: mic_recorder(start_prompt="🎤", key=f"mic_{item}")
            else: st.info("No speaking exercises.")

        with t3:
            if content["reading"]:
                for r in content["reading"]:
                    st.markdown(f'<div class="reading-box">{ " ".join(r["text"]) }</div>', unsafe_allow_html=True)
                    st.text_area("Your response:", key=f"text_{r['title']}")