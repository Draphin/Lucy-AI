import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components  # New Import
import json
import requests

# --- 1. Memory Logic ---
def load_permanent_memory():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        return dict(zip(df['Key'], df['Value']))
    except:
        return {}

# --- 2. Voice Logic (Option 3) ---
import streamlit as st
import streamlit.components.v1 as components
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖")

# --- UI HEADER ---
st.title("🤖 Lucy Engine Online")

# --- VOICE FUNCTION (THE FIX) ---
def speak(text):
    """Injects JavaScript to handle Text-to-Speech via the browser."""
    if not text:
        return
    
    # Generate a unique key using a timestamp to prevent Streamlit Duplicate Key errors
    unique_id = int(time.time() * 1000)
    
    # Use repr() to safely escape the string for JavaScript
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({repr(text)});
        window.speechSynthesis.speak(msg);
        </script>
    """
    # Render the invisible component
    components.html(js_code, height=0, key=f"voice_{unique_id}")

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHAT HISTORY DISPLAY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Speak to Lucy..."):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Response 
    # (Replace this placeholder with your actual Gemini API call logic)
    with st.chat_message("assistant"):
        try:
            # Placeholder for your model logic
            response = f"I hear you! You said: {prompt}" 
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 3. Trigger Voice
            speak(response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- 3. Interaction Logic ---
def ask_lucy(prompt, facts):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"You are Lucy. Facts: {json.dumps(facts)}. User: {prompt}"}]}]}
    
    response = requests.post(url, json=payload)
    res_json = response.json()
    if 'candidates' in res_json:
        return res_json['candidates'][0]['content']['parts'][0]['text']
    return f"⚠️ Error: {res_json.get('error', {}).get('message', 'Check Logs')}"

# --- 4. UI Setup ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖")
st.title("🤖 Lucy Engine Online")

current_facts = load_permanent_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Speak to Lucy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ask_lucy(prompt, current_facts)
        st.markdown(response)
        speak(response)  # Lucy speaks!
        st.session_state.messages.append({"role": "assistant", "content": response})
