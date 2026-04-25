import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
import requests
import time

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖")
st.title("🤖 Lucy Engine Online")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. SIMPLE VOICE LOGIC ---
def speak(text):
    """Injects a simple browser-based voice."""
    if not text:
        return
    
    # Use json.dumps to safely escape the text for JavaScript
    safe_text = json.dumps(text)
    unique_id = str(int(time.time() * 1000))
    
    js_code = f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance({safe_text});
        window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0, key=f"v_{unique_id}")

# --- 3. CORE LOGIC (Memory & AI) ---
def load_memory():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        return dict(zip(df['Key'], df['Value']))
    except:
        return {}

def ask_lucy(prompt, facts):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    context = f"You are Lucy. User Facts: {json.dumps(facts)}. User says: {prompt}"
    payload = {{"contents": [{{"parts": [{{"text": context}}]}}]}}
    
    try:
        response = requests.post(url, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "I'm having a little trouble connecting right now."

# --- 4. THE CHAT LOOP ---
current_facts = load_memory()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message Lucy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ask_lucy(prompt, current_facts)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        speak(response)
