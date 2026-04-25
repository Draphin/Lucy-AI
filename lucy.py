import streamlit as st
import streamlit.components.v1 as components
import time

# --- INITIAL SETUP ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- THE FIX: ROBUST VOICE FUNCTION ---
def speak(text):
    """Safely injects browser TTS using a unique string-based key."""
    if not text:
        return
    
    # Ensure ID is a string and uniquely generated
    unique_id = str(int(time.time() * 1000))
    
    # Safe handling of quotes and special characters
    safe_text = text.replace("'", "\\'").replace("\n", " ")
    
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance('{safe_text}');
        window.speechSynthesis.speak(msg);
        </script>
    """
    try:
        components.html(js_code, height=0, key=f"voice_comp_{unique_id}")
    except Exception:
        pass # Prevents the TypeError from stopping the whole app

# --- UI DISPLAY ---
st.title("🤖 Lucy Engine Online")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Speak to Lucy..."):
    # 1. Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant Response
    with st.chat_message("assistant"):
        # This is where your AI logic lives
        # Ensure 'full_response' is ALWAYS a string
        full_response = f"I hear you! You said: {prompt}"
        
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": str(full_response)})
        
        # 3. Trigger Voice immediately after the response is rendered
        speak(str(full_response))
