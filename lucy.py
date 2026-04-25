import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json
import os
import requests

# --- 1. Permanent Memory Logic (Google Sheets) ---
def load_permanent_memory():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        return dict(zip(df['Key'], df['Value']))
    except Exception as e:
        st.error(f"Memory Connection Error: {e}")
        return {}

# --- 2. AI Interaction Logic ---
def ask_lucy(prompt, history, facts):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return "Error: GOOGLE_API_KEY not found in Secrets."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    system_prompt = f"You are Lucy, an authentic AI collaborator. User facts: {json.dumps(facts)}"
    
    contents = [{"role": "user", "parts": [{"text": system_prompt}]}, 
                {"role": "model", "parts": [{"text": "Understood."}]}]
    contents.extend(history[-6:])
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload = {
        "contents": contents,
        "safetySettings": [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
        ]
    }
    
    try:
        # We use a 30s timeout to prevent those "Read timed out" errors
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        return "Lucy is silent. Check API quota or safety settings."
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- 3. UI Setup ---
st.set_page_config(page_title="Lucy AI", layout="wide")
st.title("🤖 Lucy Engine Online")

# Load memory from the Google Sheet
current_facts = load_permanent_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"][0]["text"])

# Handle user input
if prompt := st.chat_input("Talk to Lucy..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "parts": [{"text": prompt}]})
    
    # Send facts from the sheet to Lucy so she remembers you
    response = ask_lucy(prompt, st.session_state.messages[:-1], current_facts)
    
    with st.chat_message("model"):
        st.markdown(response)
    st.session_state.messages.append({"role": "model", "parts": [{"text": response}]})
