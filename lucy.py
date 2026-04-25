import streamlit as st
import json
import os
import requests

# --- Cloud Memory Setup ---
# We use a local file for now; it resets when the app sleeps, 
# but it's the fastest way to get you online!
FACTS_FILE = 'lucy_facts.json'

def load_facts():
    if os.path.exists(FACTS_FILE):
        with open(FACTS_FILE, 'r') as f: return json.load(f)
    return {}

def save_facts(facts):
    with open(FACTS_FILE, 'w') as f: json.dump(facts, f, indent=4)

# --- AI Logic ---
def ask_lucy(prompt, history, facts):
    # This pulls from the "Advanced Settings" secrets you'll set next
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    system_prompt = f"You are Lucy, an authentic AI collaborator. User facts: {json.dumps(facts)}"
    
    contents = [{"role": "user", "parts": [{"text": system_prompt}]}, 
                {"role": "model", "parts": [{"text": "Understood."}]}]
    contents.extend(history[-6:])
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    response = requests.post(url, json={"contents": contents}, timeout=10)
    return response.json()['candidates'][0]['content']['parts'][0]['text']

# --- UI Setup ---
st.set_page_config(page_title="Lucy AI", layout="wide")
st.title("🤖 Lucy Engine Online")

current_facts = load_facts()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"][0]["text"])

if prompt := st.chat_input("Talk to Lucy..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "parts": [{"text": prompt}]})
    
    response = ask_lucy(prompt, st.session_state.messages[:-1], current_facts)
    
    with st.chat_message("model"):
        st.markdown(response)
    st.session_state.messages.append({"role": "model", "parts": [{"text": response}]})
