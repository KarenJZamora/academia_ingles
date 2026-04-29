import streamlit as st
import os
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="English Practice Portal", layout="centered", page_icon="🇬🇧")

# --- 2. CSS ---
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;} 
    .stDeployButton {display:none;}
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    
    .reading-box {
        background-color: #f8f9fa; padding: 25px; border-radius: 15px;
        border-left: 8px solid #1E88E5; font-size: 1.1rem; line-height: 1.6;
        color: #1a1a1a; margin-bottom: 20px;
    }
    
    .exercise-question {
        font-size: 1.15rem; font-weight: 500; color: #2c3e50;
        margin-bottom: -15px; margin-top: 10px;
    }

    .stButton button { width: 100%; border-radius: 10px; font-weight: bold; }
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #888888; text-align: center;
        padding: 10px; font-family: monospace; font-size: 0.8rem;
    }
    .pos { color: #2e7d32; font-weight: bold; }
    .neg { color: #c62828; font-weight: bold; }
    .int { color: #1565c0; font-weight: bold; }
    .teacher-tip { 
        background-color: #fff3cd; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #ffc107; margin: 10px 0;
    }
    </style>
    <div class="custom-footer">Curated with heart by Karen ❤️</div>
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
        clean = text.split('(')[0].split('-')[0].replace('_', '').strip()
        tts = gTTS(text=clean, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- 4. LOGIN ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
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

# --- 5. LÓGICA DE PROCESAMIENTO ---
if st.session_state["authenticated"]:
    with st.sidebar:
        st.title("Navigation")
        lecciones = sorted([d for d in os.listdir(CLASES_DIR) if os.path.isdir(os.path.join(CLASES_DIR, d))])
        lec_sel = st.selectbox("Select Lesson:", lecciones) if lecciones else None
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    if lec_sel:
        display_logo(lec_sel)
        txt_path = os.path.join(CLASES_DIR, lec_sel, "material.txt")
        content = {"theory": [], "speaking": [], "reading": []}
        
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            
            curr_mode = None
            for l in lines:
                # Detección de Secciones Principales
                if l.startswith("[THEORY:"):
                    curr_mode = "theory"
                    content["theory"].append({"title": l[8:-1], "data": {}, "exercises": []})
                elif l.startswith("[READING:"):
                    curr_mode = "reading"
                    content["reading"].append({"title": l[9:-1], "text": []})
                
                # Manejo de Ejercicios (se quedan en la Teoría)
                elif l.startswith("[EXERCISES]") or l.startswith("[COMPLETE]") or l.startswith("[TRANSLATE]"):
                    if curr_mode == "theory" and content["theory"]:
                        content["theory"][-1]["exercises"].append({"type": "header", "val": l[1:-1]})
                    curr_mode = "theory_exercises" # Sub-modo para capturar ítems de ejercicio
                
                elif l.startswith("["):
                    # Si es cualquier otro corchete (Greetings, Colors...), es Speaking
                    curr_mode = "speaking"
                    content["speaking"].append({"title": l[1:-1], "items": []})
                
                else:
                    # Clasificación de líneas según el modo activo
                    if curr_mode == "theory":
                        tag = l.split(":")[0] if ":" in l else "TEXT"
                        val = l.split(":", 1)[1].strip() if ":" in l else l
                        if tag not in content["theory"][-1]["data"]: content["theory"][-1]["data"][tag] = []
                        content["theory"][-1]["data"][tag].append(val)
                    
                    elif curr_mode == "theory_exercises":
                        if content["theory"]:
                            content["theory"][-1]["exercises"].append({"type": "item", "val": l})
                    
                    elif curr_mode == "speaking":
                        content["speaking"][-1]["items"].append(l)
                    
                    elif curr_mode == "reading":
                        content["reading"][-1]["text"].append(l)

        # --- 6. TABS ---
        tabs = st.tabs(["📚 Theory & Practice", "🎤 Speaking Center", "✍️ Writing"])

        with tabs[0]: # Theory & Practice
            if content["theory"]:
                tema_sel = st.selectbox("🎯 Choose a topic:", [t["title"] for t in content["theory"]])
                tema = next(t for t in content["theory"] if t["title"] == tema_sel)
                st.markdown(f"## {tema['title']}")
                
                # 1. Concepto y Tipos
                if "CONCEPTO" in tema["data"]:
                    st.markdown("### 💡 Key Concept")
                    st.write(tema["data"]["CONCEPTO"][0])
                
                col_p, col_s = st.columns(2)
                if "PRONUNCIACION" in tema["data"]: col_p.info(f"🗣️ **Pronunciation:** {tema['data']['PRONUNCIACION'][0]}")
                if "SIGNIFICADO" in tema["data"]: col_s.success(f"📖 **Meaning:** {tema['data']['SIGNIFICADO'][0]}")

                # 2. Estructuras Gramaticales
                st.markdown("### 🏗️ Grammar Structures")
                with st.container(border=True):
                    for tag, label, cls in [("POSITIVE", "Positive", "pos"), ("NEGATIVE", "Negative", "neg"), ("QUESTION", "Question", "int")]:
                        if tag in tema["data"]:
                            st.markdown(f"**{label}:** <span class='{cls}'>{tema['data'][tag][0]}</span>", unsafe_allow_html=True)

                if "TIP" in tema["data"]:
                    st.markdown("### ❤️ Karen's Tip")
                    for tip in tema["data"]["TIP"]:
                        st.markdown(f"<div class='teacher-tip'>{tip}</div>", unsafe_allow_html=True)

                # 3. Contexto (Ejemplos)
                if "CONTEXTO" in tema["data"]:
                    st.markdown("### 🌟 Examples in Context")
                    for ctx in tema["data"]["CONTEXTO"]:
                        st.write(f"🔹 {ctx}")

                # 4. PRÁCTICA (Debajo de los ejemplos)
                if tema["exercises"]:
                    st.divider()
                    st.markdown("### ✍️ Quick Practice Activity")
                    for i, ex in enumerate(tema["exercises"]):
                        if ex["type"] == "header":
                            st.markdown(f"#### 📝 {ex['val']}")
                        else:
                            val = ex["val"]
                            if "(" in val and "___" in val:
                                parts = val.split("(")
                                correct = parts[1].split(")")[0].strip()
                                quest = parts[0].replace("___", "_______")
                                st.markdown(f"<p class='exercise-question'>{quest}</p>", unsafe_allow_html=True)
                                ans = st.text_input("", key=f"th_ex_{tema_sel}_{i}", placeholder="Type answer...").strip()
                                if ans:
                                    if ans.lower() == correct.lower(): st.success("Correct! ✨")
                                    else: st.error("Try again!")
                            else:
                                st.write(f"• {val}")
            else: st.info("Select a lesson.")

        with tabs[1]: # Speaking Center
            if content["speaking"]:
                # Filtramos para que no aparezcan etiquetas de ejercicios en el selector
                spk_titles = [s["title"] for s in content["speaking"]]
                spk_tema_sel = st.selectbox("🗣️ Select Vocabulary Theme:", spk_titles)
                spk_tema = next(s for s in content["speaking"] if s["title"] == spk_tema_sel)
                
                st.markdown(f"## 📍 {spk_tema['title']}")
                for i, item in enumerate(spk_tema["items"]):
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 2])
                        c1.write(f"**{item}**")
                        if c2.button("🔊", key=f"btn_spk_{spk_tema_sel}_{i}"):
                            audio = text_to_speech(item)
                            if audio: st.audio(audio, format="audio/mp3", autoplay=True)
                        with c3: mic_recorder(start_prompt="🎤", key=f"mic_spk_{spk_tema_sel}_{i}")
            else: st.info("No vocabulary sections.")

        with tabs[2]: # Writing
            if content["reading"]:
                r_idx = st.selectbox("Select Reading:", range(len(content["reading"])), format_func=lambda x: content["reading"][x]["title"])
                reading = content["reading"][r_idx]
                st.markdown(f'<div class="reading-box"><strong>{reading["title"]}</strong><br><br>{"<br>".join(reading["text"])}</div>', unsafe_allow_html=True)
                ans_text = st.text_area("Your response:", height=200, key=f"write_{r_idx}")
                if st.button("💾 Save My Work"):
                    st.success("Work saved!")