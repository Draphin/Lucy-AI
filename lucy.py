import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json
import requests

# --- 1. Permanent Memory Logic (Google Sheets) ---
def load_permanent_memory():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        df = df.dropna(subset=['Key', 'Value'])
        return dict(zip(df['Key'], df['Value']))
    except Exception as e:
        st.warning(f"Note: Memory sheet not connected. (Error: {e})")
        return {}

# --- 2. AI Interaction Logic ---
def ask_lucy(prompt, history, facts):
    try:
        # Get the key and ensure no hidden spaces
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
    except:
        return "Error: GOOGLE_API_KEY not found in Streamlit Secrets."

    # The verified URL path
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    fact_str = json.dumps(facts, indent=2) if facts else "No personal facts recorded yet."
    
    # Build the payload
    contents = []
    
    # System context as the first 'user' message
    contents.append({
        "role": "user", 
        "parts": [{"text": f"System Instruction: You are Lucy, an authentic AI collaborator with a touch of wit. User facts: {fact_str}"}]
    })
    # Required 'model' acknowledgement for turn-based chat
    contents.append({"role": "model", "parts": [{"text": "Understood. Lucy is online."}]})
    
    # Add conversation history with correct role mapping
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    # Add the current prompt
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload = {"contents": contents}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # This captures the EXACT reason for silence
            error_details = res_json.get('error', {}).get('message', 'Unknown Error')
            return f"⚠️ Lucy is silent. Reason: {error_details}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

# --- 3. UI Setup ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖", layout="wide")
st.title("🤖 Lucy Engine Online")

current_facts = load_permanent_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle Chat Input
if prompt := st.chat_input("Message Lucy..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get and display response
    with st.chat_message("model"):
        response = ask_lucy(prompt, st.session_state.messages, current_facts)
        st.markdown(response)
    
    # Save to session history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "model", "content": response})
