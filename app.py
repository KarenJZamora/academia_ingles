import streamlit as st
import os
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="English Practice Portal", layout="centered", page_icon="🇬🇧")

# --- 2. BASE DE DATOS EN SESIÓN (Persistencia simulada) ---
if "db_submissions" not in st.session_state:
    st.session_state["db_submissions"] = {} # Formato: {usuario: {leccion: {"texto": "", "nota": "", "feedback": ""}}}

# --- 3. AUTO-GRADER (Lógica de IA simulada) ---
def ai_auto_grader(user_text, lesson_name):
    words = user_text.split()
    word_count = len(words)
    
    if word_count < 10:
        return "4/10", "Your response is too short. Try to add more details and complete sentences."
    elif word_count < 25:
        return "7/10", "Good job! You followed the instructions, but you could expand your vocabulary."
    else:
        return "10/10", "Excellent! Your writing is fluent, well-structured, and shows great effort."

# --- 4. CSS (AJUSTADO PARA SUBIR EL LOGO) ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        margin-top: -60px;
    }
    #MainMenu, footer, header {visibility: hidden;} 
    .stDeployButton {display:none;}
    .stImage > img { display: block; margin-left: auto; margin-right: auto; }
    .reading-box {
        background-color: #f8f9fa; padding: 25px; border-radius: 15px;
        border-left: 8px solid #1E88E5; font-size: 1.1rem; line-height: 1.6;
        color: #1a1a1a; margin-bottom: 20px;
    }
    .exercise-question {
        font-size: 1.1rem; font-weight: 500; color: #2c3e50;
        margin-bottom: -10px; margin-top: 15px;
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

# --- 5. FUNCIONES Y RUTAS ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CLASES_DIR = os.path.join(BASE_PATH, "Clases")
USERS = {"Arianny": "password2026", "profe": "admin123", "Wilcar": "W12345"}

def display_logo(lec_sel=None):
    path = os.path.join(CLASES_DIR, "Nivel_A1", "logo.png")
    if lec_sel:
        alt_path = os.path.join(CLASES_DIR, lec_sel, "logo.png")
        if os.path.exists(alt_path): path = alt_path
    if os.path.exists(path):
        st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
        with col: st.image(path, width=200)

def text_to_speech(text):
    try:
        clean = text.split('(')[0].replace('_', '').strip()
        tts = gTTS(text=clean, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- 6. LOGIN ---
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
                    st.session_state["user"] = u
                    st.rerun()
                else: st.error("❌ Invalid credentials")
    st.stop()

# --- 7. DETECCIÓN DE CARPETAS Y CONTENIDO ---
user_now = st.session_state["user"]
content = {"theory": [], "speaking": [], "reading": [], "listening": []}
lecciones = []

if st.session_state["authenticated"]:
    with st.sidebar:
        st.title(f"Hi, {user_now}!")
        if os.path.exists(CLASES_DIR):
            lecciones = sorted([d for d in os.listdir(CLASES_DIR) if os.path.isdir(os.path.join(CLASES_DIR, d))])
        else:
            st.error(f"Error: Carpeta 'Clases' no encontrada")

        lec_sel = st.selectbox("Select Lesson:", lecciones) if lecciones else None
        
        # Panel exclusivo para el Profe
        if user_now == "profe":
            st.divider()
            st.subheader("👨‍🏫 Teacher Tools")
            view_mode = st.radio("Mode:", ["Student View", "Review All Grades"])
        else:
            view_mode = "Student View"

        st.divider()
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    # Lógica de Revisión del Profe
    if view_mode == "Review All Grades" and user_now == "profe":
        st.title("📊 Global Grade Report")
        if not st.session_state["db_submissions"]:
            st.info("No submissions yet.")
        else:
            for student, student_data in st.session_state["db_submissions"].items():
                with st.expander(f"👤 Student: {student}"):
                    for lec, work in student_data.items():
                        st.write(f"**Lesson:** {lec}")
                        st.write(f"**Grade:** {work['nota']}")
                        st.write(f"**AI Feedback:** {work['feedback']}")
                        st.text_area("Student Text:", value=work['texto'], disabled=True, key=f"view_{student}_{lec}")
        st.stop()

    if lec_sel:
        display_logo(lec_sel)
        txt_path = os.path.join(CLASES_DIR, lec_sel, "material.txt")
        
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
                elif l.startswith("[LISTENING:"):
                    curr_mode = "listening"
                    content["listening"].append({"title": l[11:-1], "items": []})
                elif l.startswith("[EXERCISES]") or l.startswith("[COMPLETE]") or l.startswith("[TRANSLATE]"):
                    curr_mode = "theory_exercises"
                    content["theory"][-1]["exercises"].append({"type": "header", "val": l[1:-1]})
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
                    elif curr_mode == "reading":
                        content["reading"][-1]["text"].append(l)
                    elif curr_mode == "listening":
                        content["listening"][-1]["items"].append(l)

        # --- TABS ---
        tabs = st.tabs(["📚 Theory & Practice", "🎤 Speaking Center", "🎧 Listening Center", "✍️ Writing", "🏆 Grades"])

        with tabs[0]: # Theory & Practice
            if content["theory"]:
                tema_sel = st.selectbox("🎯 Choose a topic:", [t["title"] for t in content["theory"]])
                tema = next(t for t in content["theory"] if t["title"] == tema_sel)
                st.markdown(f"## {tema['title']}")
                if "CONCEPTO" in tema["data"]: st.write(tema["data"]["CONCEPTO"][0])
                
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
                                user_ans = st.text_input("Answer:", key=f"th_ans_{tema_sel}_{i}", placeholder="Type answer...").strip()
                                if user_ans:
                                    if user_ans.lower() == answer.lower(): st.success("Correct! ✨")
                                    else: st.error(f"Try again!")
                            else: st.write(f"• {val}")

        with tabs[1]: # Speaking
            if content["speaking"]:
                spk_tema_sel = st.selectbox("🗣️ Theme:", [s["title"] for s in content["speaking"]])
                spk_tema = next(s for s in content["speaking"] if s["title"] == spk_tema_sel)
                for i, item in enumerate(spk_tema["items"]):
                    with st.container(border=True):
                        c1, col_v, col_m = st.columns([3, 1, 2])
                        c1.write(f"**{item}**")
                        if col_v.button("🔊", key=f"v_{spk_tema_sel}_{i}"):
                            audio = text_to_speech(item)
                            if audio: st.audio(audio, autoplay=True)
                        with col_m: mic_recorder(start_prompt="🎤", key=f"m_{spk_tema_sel}_{i}")

        with tabs[2]: # Listening
            if content["listening"]:
                lst_sel = st.selectbox("🎧 Select Listening Activity:", [l["title"] for l in content["listening"]])
                listening = next(l for l in content["listening"] if l["title"] == lst_sel)
                st.info("Listen and type exactly what you hear.")
                for i, item in enumerate(listening["items"]):
                    if "(" in item:
                        frase_audio = item.split("(")[0].strip()
                        respuesta_correcta = item.split("(")[1].split(")")[0].strip()
                        with st.container(border=True):
                            c1, c2 = st.columns([1, 4])
                            if c1.button("▶️ Play", key=f"play_{lst_sel}_{i}"):
                                audio = text_to_speech(frase_audio)
                                if audio: st.audio(audio, autoplay=True)
                            user_ans = c2.text_input("Type here:", key=f"list_ans_{lst_sel}_{i}", placeholder="..." ).strip()
                            if user_ans:
                                if user_ans.lower() == respuesta_correcta.lower(): st.success("Correct! ✨")
                                else: st.error("Try again! 👂")

        with tabs[3]: # Writing con Auto-Grader
            if content["reading"]:
                r_idx = st.selectbox("Select Reading:", range(len(content["reading"])), format_func=lambda x: content["reading"][x]["title"])
                reading = content["reading"][r_idx]
                st.markdown(f'<div class="reading-box">{reading["title"]}<br><br>{"<br>".join(reading["text"])}</div>', unsafe_allow_html=True)
                
                # Cargar texto previo si existe
                current_sub = st.session_state["db_submissions"].get(user_now, {}).get(lec_sel, {})
                user_text = st.text_area("Your response:", value=current_sub.get("texto", ""), height=200, key=f"write_{lec_sel}")
                
                if st.button("🚀 Submit & Auto-Grade"):
                    with st.spinner("AI analyzing..."):
                        nota, feedback = ai_auto_grader(user_text, lec_sel)
                        # Guardar en "DB"
                        if user_now not in st.session_state["db_submissions"]:
                            st.session_state["db_submissions"][user_now] = {}
                        st.session_state["db_submissions"][user_now][lec_sel] = {
                            "texto": user_text,
                            "nota": nota,
                            "feedback": feedback
                        }
                        st.success(f"Work Graded! Your score: {nota}")
                        st.info(f"AI Feedback: {feedback}")

        with tabs[4]: # Calificaciones para Alumnos
            st.subheader("📊 Your Academic Progress")
            my_grades = st.session_state["db_submissions"].get(user_now, {})
            if not my_grades:
                st.write("No grades yet. Submit your writing work to see results.")
            else:
                for lesson, data in my_grades.items():
                    with st.container(border=True):
                        st.write(f"📖 **Lesson:** {lesson}")
                        st.write(f"⭐ **Grade:** {data['nota']}")
                        st.write(f"💬 **Teacher/AI Feedback:** {data['feedback']}")