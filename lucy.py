import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json
import requests

# --- 1. Permanent Memory Logic (Google Sheets) ---
def load_permanent_memory():
    try:
        # Connects using the GSHEET_URL in Streamlit Secrets
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        df = df.dropna(subset=['Key', 'Value'])
        return dict(zip(df['Key'], df['Value']))
    except Exception as e:
        st.warning(f"Note: Memory sheet not connected. (Error: {e})")
        return {}

# --- 2. AI Interaction Logic ---
def ask_lucy(prompt, history, facts):
    # Get key and strip any accidental spaces from the Secret
    try:
        raw_key = st.secrets["GOOGLE_API_KEY"]
        api_key = raw_key.strip()
    except:
        return "Error: GOOGLE_API_KEY not found in Streamlit Secrets."

    # Using the stable v1 endpoint and 1.5-flash model
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + api_key
    
    fact_str = json.dumps(facts, indent=2) if facts else "No personal facts recorded yet."
    
    system_prompt = (
        "You are Lucy, an authentic AI collaborator with a touch of wit. "
        "Be insightful, clear, and concise. Use these facts to remember the user: "
        f"{fact_str}"
    )
    
    # Structure the conversation for the API
    contents = [
        {"role": "user", "parts": [{"text": system_prompt}]}, 
        {"role": "model", "parts": [{"text": "Understood. Lucy is online."}]}
    ]
    
    # Add history and current prompt
    contents.extend(history[-6:])
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
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
            error_details = res_json.get('error', {}).get('message', 'Check API Key or Quota.')
            return f"⚠️ Lucy is silent. Reason: {error_details}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

# --- 3. UI Setup ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖", layout="wide")
st.title("🤖 Lucy Engine Online")

# Initial memory load
current_facts = load_permanent_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    # --- 3. UI Setup ---
st.set_page_config(page_title="Lucy AI", page_icon="🤖", layout="wide")
st.title("🤖 Lucy Engine Online")

# Initial memory load
current_facts = load_permanent_memory()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["parts"][0]["text"])

# Handle Chat Input
if prompt := st.chat_input("Message Lucy..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prep history for the API call
    api_history = st.session_state.messages.copy()
    
    with st.chat_message("model"):
        response = ask_lucy(prompt, api_history, current_facts)
        st.markdown(response)
    
    # Save to history
    st.session_state.messages.append({"role": "user", "parts": [{"text": prompt}]})
    st.session_state.messages.append({"role": "model", "parts": [{"text": response}]})
    with st.chat_message(msg["role"]):
        st.markdown
