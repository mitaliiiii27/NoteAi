import streamlit as st
import requests

# Set page config first
st.set_page_config(page_title="Autocomplete Notepad with LLM (API)", layout="wide")
st.title("📝 Notepad with LLM Autocomplete (via Together.ai)")

# 🔐 Use your own Together.ai API key (recommended to store in secrets)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

# Initialize notepad session state
if "notepad_text" not in st.session_state:
    st.session_state.notepad_text = ""

# File upload (open file)
uploaded_file = st.file_uploader("📂 Open .txt File", type=["txt"])
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    st.session_state.notepad_text = content
    st.success("File loaded successfully!")

# Model selection
model = st.selectbox("Choose LLM model", [
    "deepseek-ai/DeepSeek-V3",
    "mistralai/Mistral-7B-Instruct-v0.1",
    "meta-llama/Llama-2-7b-chat-hf",
])

# Text input area
text_input = st.text_area("Type here:", st.session_state.notepad_text, height=300)

# API call function
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

# Buttons row
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔮 Autocomplete"):
        with st.spinner("Generating..."):
            completion = get_autocomplete(text_input.strip(), model)
        st.session_state.notepad_text = text_input + completion
        st.rerun()

with col2:
    st.download_button(
        label="💾 Save Notepad",
        data=st.session_state.notepad_text,
        file_name="notepad.txt",
        mime="text/plain"
    )

with col3:
    if st.button("🗑️ Clear Notepad"):
        st.session_state.notepad_text = ""
        st.rerun()

# Keep session updated
st.session_state.notepad_text = text_input
