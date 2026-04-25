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
def speak(text):
    # This script looks for a female-sounding voice before speaking
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance('{text.replace("'", "")}');
        
        // Function to find and set a female voice
        function setVoice() {{
            var voices = window.speechSynthesis.getVoices();
            // Look for common female voice names
            var femaleVoice = voices.find(voice => 
                voice.name.includes('Female') || 
                voice.name.includes('Zira') || 
                voice.name.includes('Google US English') ||
                voice.name.includes('Samantha') ||
                voice.name.includes('Victoria')
            );
            
            if (femaleVoice) {{
                msg.voice = femaleVoice;
            }}
            window.speechSynthesis.speak(msg);
        }}

        // Voices are loaded async, so we handle both cases
        if (window.speechSynthesis.getVoices().length !== 0) {{
            setVoice();
        }} else {{
            window.speechSynthesis.onvoiceschanged = setVoice;
        }}
        </script>
    """
    components.html(js_code, height=0)

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
