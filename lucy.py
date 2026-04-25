import streamlit as st
import streamlit.components.v1 as components
import time

# 1. Page Config
st.set_page_config(page_title="Lucy AI", page_icon="🤖")

# 2. Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_speech" not in st.session_state:
    st.session_state.last_speech = None

# 3. Voice Function (No 'key' argument needed for html if used correctly)
def speak(text):
    if not text or st.session_state.last_speech == text:
        return
    
    # Store to prevent repeat triggers on every re-run
    st.session_state.last_speech = text
    
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({repr(text)});
        window.speechSynthesis.speak(msg);
        </script>
    """
    # Use a unique key based on the text hash + timestamp to keep it stable
    components.html(js_code, height=0, key=f"speech_{hash(text)}_{int(time.time())}")

# 4. UI Layout
st.title("🤖 Lucy Engine Online")

# Display historical messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Chat Input logic
if prompt := st.chat_input("Speak to Lucy..."):
    # Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        # PLACEHOLDER: Replace with your Gemini API call
        full_response = f"I hear you! You said: {prompt}"
        
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # We don't call speak() here; we let the script finish and handle it below

# 6. Audio Trigger (Last step)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak(st.session_state.messages[-1]["content"])
