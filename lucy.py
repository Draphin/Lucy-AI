import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
import requests
import time # Added for stability

# --- 1. Memory Logic ---
def load_permanent_memory():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        return dict(zip(df['Key'], df['Value']))
    except:
        return {}

# --- 2. Voice Logic (Improved Option 3) ---
def speak(text):
    # json.dumps ensures the text doesn't break the JavaScript
    safe_text = json.dumps(text)
    unique_id = int(time.time())
    
    js_code = f"""
        <script>
        function executeSpeak() {{
            window.speechSynthesis.cancel(); 
            var msg = new SpeechSynthesisUtterance({safe_text});
            var voices = window.speechSynthesis.getVoices();
            
            // Priority list for female voices - condensed to one line for stability
            var femaleVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Zira') || v.name.includes('Google US English') || v.name.includes('Samantha'));
            
            if (femaleVoice) msg.voice = femaleVoice;
            msg.pitch = 1.1; 
            window.speechSynthesis.speak(msg);
        }}

        if (window.speechSynthesis.getVoices().length !== 0) {{
            executeSpeak();
        }} else {{
            window.speechSynthesis.onvoiceschanged = executeSpeak;
        }}
        </script>
    """
    # unique key prevents Streamlit from skipping the render
    components.html(js_code, height=0, key=f"voice_{unique_id}")
    
# --- 3. Interaction Logic ---
def ask_lucy(prompt, facts):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # Updated to 2.0-flash for better performance
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"You are Lucy. Facts: {json.dumps(facts)}. User: {prompt}"}]}]}
    
    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except:
        return "I'm having a momentary lapse in connection. Could you try that again?"

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
        speak(response) 
        st.session_state.messages.append({"role": "assistant", "content": response})
