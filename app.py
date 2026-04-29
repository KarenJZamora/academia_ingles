import streamlit as st
import os
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(page_title="English Practice Portal", layout="centered", page_icon="🇬🇧")

# --- 2. CSS PARA OCULTAR INTERFAZ (Solución Definitiva para Foto y User) ---
st.markdown("""
    <style>
    /* Oculta el encabezado superior */
    header {visibility: hidden !important; height: 0px !important;}
    
    /* ELIMINA LA BARRA INFERIOR DERECHA (Foto y "Created by") */
    /* Este bloque apunta a los contenedores específicos de la nube */
    [data-testid="stStatusWidget"] {display: none !important;}
    .stViewerBadge {display: none !important;}
    #streamlit_viewer_badge {display: none !important;}
    
    /* Oculta el botón rojo de "Hosted with Streamlit" */
    footer {display: none !important;}
    .stAppDeployButton {display: none !important;}
    
    /* Oculta cualquier barra de herramientas flotante */
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}

    /* Ajuste para que el contenido no se pegue arriba */
    .block-container {padding-top: 1rem !important;}

    /* Tu firma personalizada al centro */
    .custom-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #888888; text-align: center;
        padding: 10px; font-family: monospace; font-size: 0.8rem;
    }
    </style>
    <div class="custom-footer">Curated with heart by Karen ❤️</div>
    """, unsafe_allow_html=True)

# --- 3. FUNCIONES DE APOYO ---
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
    # Ajustamos la ruta para que busque el logo en tu nueva carpeta Nivel_A1
    path_login = os.path.join(CLASES_DIR, "Nivel_A1", "logo.png")
    
    if os.path.exists(path_login):
        _, col, _ = st.columns([1, 1, 1])
        with col: 
            st.image(path_login, width=220)
    else:
        # Si no encuentra el logo en Nivel_A1, ponemos un título de respaldo
        st.markdown("<h1 style='text-align:center;'>🇬🇧 English Classes</h1>", unsafe_allow_html=True)
    
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
                else: 
                    st.error("❌ Invalid credentials")
    st.stop()

# --- 5. PROCESAMIENTO DE CONTENIDO ---
if st.session_state["authenticated"]:
    with st.sidebar:
        st.title("Navigation")
        # Listar carpetas dentro de Clases para crear el menú
        if os.path.exists(CLASES_DIR):
            lecciones = sorted([d for d in os.listdir(CLASES_DIR) if os.path.isdir(os.path.join(CLASES_DIR, d))])
        else:
            lecciones = []
            
        if lecciones:
            # Aquí se crea el desplegable
            lec_sel = st.selectbox("Select Level:", lecciones)
        else:
            st.error("No se encontraron carpetas. Revisa la carpeta 'Clases'")
            lec_sel = None

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
                if l.startswith("[THEORY:"):
                    curr_mode = "theory"
                    content["theory"].append({"title": l[8:-1], "data": {}, "exercises": []})
                elif l.startswith("[READING:"):
                    curr_mode = "reading"
                    content["reading"].append({"title": l[9:-1], "text": []})
                elif l.startswith("[EXERCISES]") or l.startswith("[COMPLETE]") or l.startswith("[TRANSLATE]"):
                    if curr_mode == "theory" or curr_mode == "theory_exercises":
                        content["theory"][-1]["exercises"].append({"type": "header", "val": l[1:-1]})
                        curr_mode = "theory_exercises"
                elif l.startswith("["):
                    curr_mode = "speaking"
                    content["speaking"].append({"title": l[1:-1], "items": []})
                else:
                    if curr_mode == "theory":
                        tag = l.split(":")[0] if ":" in l else "TEXT"
                        val = l.split(":", 1)[1].strip() if ":" in l else l
                        if tag not in content["theory"][-1]["data"]: content["theory"][-1]["data"][tag] = []
                        content["theory"][-1]["data"][tag].append(val)
                    elif curr_mode == "theory_exercises":
                        content["theory"][-1]["exercises"].append({"type": "item", "val": l})
                    elif curr_mode == "speaking":
                        content["speaking"][-1]["items"].append(l)
                    elif curr_mode == "reading": # <--- CAMBIAR section POR mode
                        content["reading"][-1]["text"].append(l)
        # --- TABS ---
        tabs = st.tabs(["📚 Theory & Practice", "🎤 Speaking Center", "✍️ Writing"])

        with tabs[0]:
            if content["theory"]:
                tema_sel = st.selectbox("🎯 Choose a topic:", [t["title"] for t in content["theory"]])
                tema = next(t for t in content["theory"] if t["title"] == tema_sel)
                st.markdown(f"## {tema['title']}")
                
                if "CONCEPTO" in tema["data"]:
                    st.markdown("### 💡 Key Concept")
                    st.write(tema["data"]["CONCEPTO"][0])
                
                col_p, col_s = st.columns(2)
                if "PRONUNCIACION" in tema["data"]: col_p.info(f"🗣️ **Pronunciation:** {tema['data']['PRONUNCIACION'][0]}")
                if "SIGNIFICADO" in tema["data"]: col_s.success(f"📖 **Meaning:** {tema['data']['SIGNIFICADO'][0]}")

                st.markdown("### 🏗️ Grammar Structures")
                with st.container(border=True):
                    if "POSITIVE" in tema["data"]: st.markdown(f"➕ <span class='pos'>Positive:</span> `{tema['data']['POSITIVE'][0]}`", unsafe_allow_html=True)
                    if "NEGATIVE" in tema["data"]: st.markdown(f"➖ <span class='neg'>Negative:</span> `{tema['data']['NEGATIVE'][0]}`", unsafe_allow_html=True)
                    if "QUESTION" in tema["data"]: st.markdown(f"❓ <span class='int'>Question:</span> `{tema['data']['QUESTION'][0]}`", unsafe_allow_html=True)

                if "TIP" in tema["data"]:
                    st.markdown("### ❤️ Karen's Tip")
                    for tip in tema["data"]["TIP"]:
                        st.markdown(f"<div class='teacher-tip'>{tip}</div>", unsafe_allow_html=True)

                if "CONTEXTO" in tema["data"]:
                    st.markdown("### 🌟 Examples in Context")
                    for ctx in tema["data"]["CONTEXTO"]: st.write(f"🔹 {ctx}")

                if tema["exercises"]:
                    st.divider()
                    st.markdown("### ✍️ Practice Activities")
                    for i, ex in enumerate(tema["exercises"]):
                        if ex["type"] == "header":
                            st.markdown(f"#### 📝 {ex['val']}")
                        else:
                            val = ex["val"]
                            if "(" in val:
                                parts = val.split("(")
                                question = parts[0].replace("___", "_______").strip()
                                answer = parts[1].split(")")[0].strip()
                                st.markdown(f"<p class='exercise-question'>{question}</p>", unsafe_allow_html=True)
                                user_ans = st.text_input("", key=f"th_ans_{tema_sel}_{i}", placeholder="Type answer...").strip()
                                if user_ans:
                                    if user_ans.lower() == answer.lower(): st.success("Correct! ✨")
                                    else: st.error(f"Try again!")
                            else: st.write(f"• {val}")

        with tabs[1]:
            if content["speaking"]:
                spk_tema_sel = st.selectbox("🗣️ Select Theme:", [s["title"] for s in content["speaking"]])
                spk_tema = next(s for s in content["speaking"] if s["title"] == spk_tema_sel)
                st.markdown(f"## 📍 {spk_tema['title']}")
                for i, item in enumerate(spk_tema["items"]):
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 2])
                        c1.write(f"**{item}**")
                        if c2.button("🔊", key=f"btn_v_{spk_tema_sel}_{i}"):
                            audio = text_to_speech(item)
                            if audio: st.audio(audio, format="audio/mp3", autoplay=True)
                        with c3: mic_recorder(start_prompt="🎤", key=f"mic_v_{spk_tema_sel}_{i}")

        with tabs[2]:
            if content["reading"]:
                r_idx = st.selectbox("Select Reading:", range(len(content["reading"])), format_func=lambda x: content["reading"][x]["title"])
                reading = content["reading"][r_idx]
                st.markdown(f'<div class="reading-box"><strong>{reading["title"]}</strong><br><br>{"<br>".join(reading["text"])}</div>', unsafe_allow_html=True)
                st.text_area("Your response:", height=200, key=f"write_{r_idx}")
                if st.button("💾 Save My Work"): st.success("Saved!")