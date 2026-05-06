import streamlit as st
import requests
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import io

# ----------------- Page Config -----------------
st.set_page_config(page_title="Autocomplete Notepad with LLM (API)", layout="wide")

# ----------------- Session State Initialization -----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "notepad_text" not in st.session_state:
    st.session_state.notepad_text = ""

if "text_input" not in st.session_state:
    st.session_state.text_input = st.session_state.notepad_text

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "history" not in st.session_state:
    st.session_state.history = [st.session_state.notepad_text]

if "history_index" not in st.session_state:
    st.session_state.history_index = 0

try:
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
except:
    TOGETHER_API_KEY = ""

# ----------------- Theme -----------------
def apply_theme():
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
        .stApp { background-color: #0a1220; color: #e0e0e0; }
        .stTextArea textarea { background-color: #141b2d !important; color: #e0e0e0 !important; border: 1px solid #22304a !important; }
        .stSelectbox select { background-color: #141b2d !important; color: #e0e0e0 !important; }
        .stButton button { background-color: #1f2a44 !important; color: #e0e0e0 !important; border: 1px solid #2c3e63 !important; }
        .stButton button:hover { background-color: #2c3e63 !important; border: 1px solid #3b5285 !important; }
        h1, h2, h3, h4, h5, h6 { color: #f0f0f0 !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #ffffff; color: #000000; }</style>", unsafe_allow_html=True)

apply_theme()

# ----------------- Header -----------------
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("📝 Notepad with LLM Autocomplete & Voice Input")
with header_col2:
    theme_icon = "🌙" if not st.session_state.dark_mode else "☀️"
    if st.button(f"{theme_icon} Dark Mode" if not st.session_state.dark_mode else f"{theme_icon} Light Mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ----------------- Helper Functions -----------------
def sync_notepad_text(text):
    st.session_state.notepad_text = text
    st.session_state.text_input = text

def add_to_history(text):
    current_entry = st.session_state.history[st.session_state.history_index] if 0 <= st.session_state.history_index < len(st.session_state.history) else ""
    if text == current_entry:
        return
    if st.session_state.history_index < len(st.session_state.history) - 1:
        st.session_state.history = st.session_state.history[:st.session_state.history_index + 1]
    st.session_state.history.append(text)
    st.session_state.history_index = len(st.session_state.history) - 1
    if len(st.session_state.history) > 50:
        st.session_state.history.pop(0)
        st.session_state.history_index = len(st.session_state.history) - 1

def undo():
    if st.session_state.history_index > 0:
        st.session_state.history_index -= 1
        sync_notepad_text(st.session_state.history[st.session_state.history_index])

def redo():
    if st.session_state.history_index < len(st.session_state.history) - 1:
        st.session_state.history_index += 1
        sync_notepad_text(st.session_state.history[st.session_state.history_index])

# ----------------- Autocomplete Function -----------------
def get_autocomplete(prompt, model_name):
    url = "https://api.together.xyz/v1/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "prompt": f"You are a helpful writing assistant. Continue the following text:\n\n{prompt}",
        "max_tokens": 50,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["\n"]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['text']
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
        return ""

# ----------------- File Upload -----------------
uploaded_file = st.file_uploader("📂 Open .txt File", type=["txt"])
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    sync_notepad_text(content)
    add_to_history(content)
    st.success("File loaded successfully!")

# ----------------- LLM Model Selection -----------------
model = st.selectbox("Choose LLM model", [
    "deepseek-ai/DeepSeek-V3",
    "meta-llama/Llama-2-7b-chat-hf",
])

# ----------------- Voice Input -----------------
def transcribe_audio(audio_bytes):
    recognizer = sr.Recognizer()
    try:
        audio_file = sr.AudioFile(io.BytesIO(audio_bytes))
        with audio_file as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "[Could not understand audio]"
    except sr.RequestError as e:
        return f"[Error: {str(e)}]"
    except Exception as e:
        return f"[Error processing audio: {str(e)}]"

def parse_voice_command(text):
    text_lower = text.lower()
    if "autocomplete" in text_lower or "auto complete" in text_lower:
        return "autocomplete"
    elif "clear" in text_lower and ("notepad" in text_lower or "all" in text_lower or "everything" in text_lower):
        return "clear"
    elif "undo" in text_lower:
        return "undo"
    elif "redo" in text_lower:
        return "redo"
    elif "save" in text_lower and ("file" in text_lower or "notepad" in text_lower):
        return "save"
    else:
        return None

st.subheader("🎤 Voice Input & Commands")
st.markdown("**Voice Commands**: Say 'autocomplete', 'clear notepad', 'undo', 'redo', or 'save file'")

audio_bytes = audio_recorder(
    text="Click to record",
    recording_color="#e74c3c",
    neutral_color="#3498db",
    icon_name="microphone",
    icon_size="2x",
)

if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.audio(audio_bytes, format="audio/wav")
    st.session_state.last_audio = audio_bytes
    with st.spinner("Transcribing your speech..."):
        transcribed_text = transcribe_audio(audio_bytes)
    if transcribed_text and not transcribed_text.startswith("["):
        st.success(f"Transcribed: {transcribed_text}")
        command = parse_voice_command(transcribed_text)
        if command:
            st.info(f"🎯 Voice Command Detected: {command.upper()}")
            if command == "autocomplete":
                if TOGETHER_API_KEY:
                    with st.spinner("Generating autocomplete..."):
                        completion = get_autocomplete(st.session_state.notepad_text.strip(), model)
                    new_text = st.session_state.notepad_text + completion
                    sync_notepad_text(new_text)
                    add_to_history(new_text)
                else:
                    st.error("Please add your TOGETHER_API_KEY to secrets.")
            elif command == "clear":
                sync_notepad_text("")
                add_to_history("")
            elif command == "undo":
                undo()
            elif command == "redo":
                redo()
            elif command == "save":
                st.info("Use the Save button below to download your notepad.")
        else:
            new_text = st.session_state.notepad_text + " " + transcribed_text if st.session_state.notepad_text else transcribed_text
            sync_notepad_text(new_text)
            add_to_history(new_text)
        st.rerun()
    else:
        st.error(transcribed_text)

# ----------------- BUTTONS (Aligned Perfectly) -----------------
cols = st.columns([1, 1, 1, 1, 1], gap="small")

with cols[0]:
    if st.button("🔮 Autocomplete", use_container_width=True):
        if not TOGETHER_API_KEY:
            st.error("Please add your TOGETHER_API_KEY to secrets.")
        else:
            with st.spinner("Generating..."):
                completion = get_autocomplete(st.session_state.notepad_text.strip(), model)
            new_text = st.session_state.notepad_text + completion
            sync_notepad_text(new_text)
            add_to_history(new_text)
            st.rerun()

with cols[1]:
    if st.button("↶ Undo", disabled=st.session_state.history_index <= 0, use_container_width=True):
        undo()
        st.rerun()

with cols[2]:
    if st.button("↷ Redo", disabled=st.session_state.history_index >= len(st.session_state.history) - 1, use_container_width=True):
        redo()
        st.rerun()

with cols[3]:
    st.download_button(
        label="💾 Save",
        data=st.session_state.notepad_text,
        file_name="notepad.txt",
        mime="text/plain",
        use_container_width=True
    )

with cols[4]:
    if st.button("🗑️ Clear", use_container_width=True):
        sync_notepad_text("")
        add_to_history("")
        st.rerun()

# ----------------- Text Area -----------------
def on_text_change():
    new_text = st.session_state.text_input
    st.session_state.notepad_text = new_text
    add_to_history(new_text)

st.text_area(
    "Type or speak here:",
    height=300,
    key="text_input",
    on_change=on_text_change
)

# ----------------- Instructions -----------------
st.markdown("---")
st.markdown(f"""
**How to use:**
- 🎤 **Voice Input**: Click the microphone to record speech.
- 🎯 **Voice Commands**: autocomplete, clear notepad, undo, redo, save file.
- ⌨️ **Type** directly in the box.
- 🔮 **Autocomplete**: Let the AI continue your text.
- ↶↷ **Undo/Redo**: Navigate text history.
- 💾 **Save**: Download your file.
- 🗑️ **Clear**: Remove all text.
- {theme_icon} **Theme**: Toggle dark/light.

**History**: {st.session_state.history_index + 1}/{len(st.session_state.history)} states
""")
