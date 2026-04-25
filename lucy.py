import streamlit as st
import json
import os
import requests

FACTS_FILE = 'lucy_facts.json'

def load_facts():
    if os.path.exists(FACTS_FILE):
        with open(FACTS_FILE, 'r') as f: return json.load(f)
    return {}

def save_facts(facts):
    with open(FACTS_FILE, 'w') as f: json.dump(facts, f, indent=4)

def ask_lucy(prompt, history, facts):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return "Error: GOOGLE_API_KEY not found in Streamlit Secrets."

    # Using the 2026 preview model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    
    system_prompt = f"You are Lucy, an authentic AI collaborator. User facts: {json.dumps(facts)}"
    
    contents = [{"role": "user", "parts": [{"text": system_prompt}]}, 
                {"role": "model", "parts": [{"text": "Understood."}]}]
    contents.extend(history[-6:])
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    # Adding safety settings to prevent unnecessary filtering
    payload = {
        "contents": contents,
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json and res_json['candidates']:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            error_details = res_json.get('error', {}).get('message', 'Lucy hit a safety filter.')
            return f"⚠️ Lucy Notice: {error_details}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"
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
