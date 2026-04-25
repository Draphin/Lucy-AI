import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json
import os
import requests

# --- 1. Permanent Memory Logic (Google Sheets) ---
def load_permanent_memory():
    try:
        # Connects using the GSHEET_URL found in your Streamlit Secrets
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        # Cleans the data to ensure no empty rows break the AI
        df = df.dropna(subset=['Key', 'Value'])
        return dict(zip(df['Key'], df['Value']))
    except Exception as e:
        # If the sheet is missing or the URL is wrong, we show a helpful warning
        st.warning(f"Note: Could not load memory sheet. (Error: {e})")
        return {}

# --- 2. AI Interaction Logic ---
def ask_lucy(prompt, history, facts):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return "Error: GOOGLE_API_KEY not found in Streamlit Secrets."

    # Using the stable 1.5-flash for better reliability
    url = f"https://generativelanguage.googleapis.com/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # We turn the spreadsheet facts into a readable string for Lucy
    fact_str = json.dumps(facts, indent=2) if facts else "No personal facts recorded yet."
    
    system_prompt = (
        "You are Lucy, an authentic AI collaborator with a touch of wit. "
        "Be insightful, clear, and concise. Use the following user facts to personalize "
        "your help, but don't be creepy about it. "
        f"User Facts: {fact_str}"
    )
    
    # Building the conversation structure
    contents = [
        {"role": "user", "parts": [{"text": system_prompt}]}, 
        {"role": "model", "parts": [{"text": "Understood. I am ready to assist as Lucy."}]}
    ]
    
    # Add recent history (last 6 messages) for context
    contents.extend(history[-6:])
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    # Relaxed safety settings to prevent "Silent Lucy"
    payload = {
        "contents": contents,
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json and res_json['candidates']:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # If the AI returns nothing, we show the raw error for debugging
            error_msg = res_json.get('error', {}).get('message', 'Unknown API Error or Safety Block.')
            return f"⚠️ Lucy is currently silent. Reason: {error_msg}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

# --- 3. UI Setup ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖", layout="wide")
st.title("🤖 Lucy Engine Online")

# Initial memory load
current_facts = load_permanent_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the chat window
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"][0]["text"])

# Handle the chat input
if prompt := st.chat_input("Message Lucy..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "parts": [{"text": prompt}]})
    
    # Get and display Lucy's response
    with st.chat_message("model"):
        response = ask_lucy(prompt, st.session_state.messages[:-1], current_facts)
        st.markdown(response)
    st.session_state.messages.append({"role": "model", "parts": [{"text": response}]})
