import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
import requests
import time  # This was likely the missing piece!

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖", layout="centered")
st.title("🤖 Lucy Engine Online")

# Ensure session state for memory and voice tracking
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_speech" not in st.session_state:
    st.session_state.last_speech = ""

# --- 2. VOICE LOGIC (Invisible & Female) ---
def speak(text):
    if not text or st.session_state.last_speech == text:
        return
    
    st.session_state.last_speech = text
    # Clean text for JavaScript
    safe_text = json.dumps(text)
    unique_id = int(time.time())
    
    js_code = f"""
        <script>
        function executeSpeak() {{
            window.speechSynthesis.cancel(); 
            var msg = new SpeechSynthesisUtterance({safe_text});
            
            var voices = window.speechSynthesis.getVoices();
            // Search for a female-toned voice
            var femaleVoice = voices.find(v => 
                (v.name.includes('Female') || v.name.includes('Zira') || 
                 v.name.includes('Google US English') || v.name.includes('Samantha') ||
                 v.name.includes('Victoria')) && v.lang.includes('en')
            );
            
            if (femaleVoice) {{
                msg.voice = femaleVoice;
            }}
            
            msg.pitch = 1.15; 
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
        }}

        // Handle async voice loading
        if (window.speechSynthesis.getVoices().length !== 0) {{
            executeSpeak();
        }} else {{
            window.speechSynthesis.onvoiceschanged = executeSpeak;
        }}
        </script>
    """
    # Unique key forces Streamlit to update the component and trigger the JS
    components.html(js_code, height=0, key=f"voice_trigger_{unique_id}")

# --- 3. MEMORY & DATA ---
def load_permanent_memory():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        return dict(zip(df['Key'], df['Value']))
    except Exception as e:
        # Don't crash if sheets fail, just return empty memory
        return {}

def ask_lucy(prompt, facts):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # Using the latest Gemini 2.0 Flash model
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    context = f"You are Lucy, a supportive and helpful AI. Facts about the user: {json.dumps(facts)}. User says: {prompt}"
    payload = {"contents": [{"parts": [{"text": context}]}]}
    
    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return "I'm having a little trouble connecting to my brain right now. Can you try that again?"

# --- 4. THE CHAT LOOP ---
current_facts = load_permanent_memory()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Message Lucy..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Lucy's response
    with st.chat_message("assistant"):
        response = ask_lucy(prompt, current_facts)
        st.markdown(response)
        speak(response) # This triggers the voice in the browser
        st.session_state.messages.append({"role": "assistant", "content": response})
