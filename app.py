import streamlit as st
import requests
import json
import base64
import time
from PIL import Image
import os
from dotenv import load_dotenv
import hashlib
from pymongo import MongoClient # Import for MongoDB

# --- Load Environment Variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- MONGODB CONNECTION SETUP ---
# Database configuration details
DB_NAME = "sample_mflix"       #  Your database name
COLLECTION_NAME = "User_credentials" #  Your collection name

@st.cache_resource
def init_connection():
    """Initializes the MongoDB connection using the URI."""
    if not MONGO_URI:
        st.error("Error: MONGO_URI not found in .env file.")
        st.stop()
    try:
        # Client handles connection pooling and management
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        return db[COLLECTION_NAME]
    except Exception as e:
        # You may see this error if the URI is incorrect or network access is blocked
        st.sidebar.error(f"Error connecting to MongoDB Atlas: {e}")
        st.stop()

# Initialize the collection object (cached connection)
user_collection = init_connection()

# --- Authentication Constants ---
AUTH_STATUS_KEY = "authenticated"
USERNAME_KEY = "username"
NAME_KEY = "name"

# --- Configuration (remains the same) ---
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-preview-09-2025:generateContent"
)
SYSTEM_INSTRUCTION = (
    "You are a friendly, helpful, and concise multimodal AI assistant. "
    "Provide detailed and accurate responses, especially when analyzing uploaded images."
)

# --- Helper Functions (remain the same) ---
def base64_encode_image(uploaded_file):
    """Encodes an uploaded Streamlit file to a base64 string and determines its mime type."""
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        encoded_string = base64.b64encode(file_bytes).decode("utf-8")
        return encoded_string, mime_type
    return None, None


def _get_gemini_response(api_key, chat_history, user_prompt, image_data=None, mime_type=None, max_retries=3):
    """Calls the Gemini API with full chat history and handles multimodal inputs."""
    if not api_key:
        st.error("Error: Gemini API Key is not set.")
        return None

    contents = []
    for role, text in chat_history[-10:]:
        contents.append({"role": role, "parts": [{"text": text}]})

    user_parts = [{"text": user_prompt}]
    if image_data and mime_type:
        user_parts.insert(0, {"inlineData": {"mimeType": mime_type, "data": image_data}})
    contents.append({"role": "user", "parts": user_parts})

    payload = {"contents": contents, "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]}}
    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries):
        try:
            with st.spinner("Generating response..."):
                response = requests.post(
                    f"{GEMINI_API_URL}?key={api_key}",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=60,
                )
            response.raise_for_status()
            result = response.json()
            candidate = result.get("candidates", [{}])[0]
            if candidate and candidate.get("content", {}).get("parts", [{}])[0].get("text"):
                return candidate["content"]["parts"][0]["text"]
            return "Error: Could not extract text from the Gemini response."

        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.ConnectionError:
            st.error("Connection error. Check your network or API endpoint.")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                st.error(f"Failed to connect to the API after {max_retries} attempts: {e}")
                return None
    return None

# --- MongoDB Authentication Function ---
def check_password():
    """Renders the login form and checks credentials against MongoDB."""
    st.set_page_config(page_title="EV Chatbot Login", layout="centered")
    st.title("🔐 EV Chatbot Login")
    
    with st.form("Login Form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # 1. Fetch user data from MongoDB
            # Assuming your user documents have fields: "username", "name", and "password_hash"
            user_data = user_collection.find_one({"username": username})

            if user_data:
                # 2. Verify password hash
                # NOTE: Ensure the password_hash field in your MongoDB collection holds SHA256 hashes!
                submitted_hash = hashlib.sha256(password.encode()).hexdigest()
                
                if submitted_hash == user_data.get("password_hash"):
                    # Success
                    st.session_state[AUTH_STATUS_KEY] = True
                    st.session_state[USERNAME_KEY] = user_data["username"]
                    st.session_state[NAME_KEY] = user_data["name"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Username not found.")
    
    return st.session_state.get(AUTH_STATUS_KEY, False)


# --- Main Application Logic (Runs ONLY if Authenticated) ---
def main_app():
    # Retrieve user data from session state
    username = st.session_state[USERNAME_KEY]
    name = st.session_state[NAME_KEY]

    st.set_page_config(page_title="EV Chatbot", layout="wide")
    st.title(f"⚡ EV Chatbot - Welcome {name}")

    # --- Sidebar ---
    with st.sidebar:
        if st.button('Logout', key='logout_btn'):
            st.session_state.clear()
            st.rerun()

        # Changed to normal font as requested
        st.markdown(f"Logged in as: {username}") 
        
        st.header("Configuration")

        if GEMINI_API_KEY:
            st.success("API KEY Integrated")
        else:
            st.warning("API KEY not found")

        st.subheader("Upload File")
        uploaded_file = st.file_uploader("Give Reference", type=["png", "jpg", "jpeg"], key="file_uploader") 

        if uploaded_file and uploaded_file.type.startswith('image'):
             st.image(uploaded_file, caption="Uploaded Image Preview", use_column_width=True)

        # Clear chat history button
        if st.button("Clear History", key="clear_chat"):
            st.session_state.messages = []
            st.rerun() 

    # --- Initialize chat state ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
        greeting = f"Hello {name}! I’m a Multimodal AI. Feel free to upload an image for analysis."
        if not GEMINI_API_KEY:
            greeting += "\n\n**Note:** Missing API key. Please check your `.env` file."
        st.session_state.messages.append(("model", greeting))

    # --- Chat Display ---
    for role, text in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(text)

    # --- User Input ---
    if user_prompt := st.chat_input("Ask me anything...", disabled=not GEMINI_API_KEY):
        image_data, mime_type = None, None

        with st.chat_message("user"):
            st.markdown(user_prompt)
            if uploaded_file and uploaded_file.type.startswith('image'):
                try:
                    uploaded_file.seek(0) 
                    img = Image.open(uploaded_file)
                    st.image(img, caption="Reference Image", width=200)
                    uploaded_file.seek(0)
                    image_data, mime_type = base64_encode_image(uploaded_file)
                except Exception as e:
                    st.error(f"Could not process image: {e}")

        st.session_state.messages.append(("user", user_prompt))
        api_history = [(r, t) for r, t in st.session_state.messages if r in ("user", "model")]

        ai_response = _get_gemini_response(GEMINI_API_KEY, api_history, user_prompt, image_data, mime_type)

        if ai_response:
            with st.chat_message("model"):
                st.markdown(ai_response)
            st.session_state.messages.append(("model", ai_response))


# --- Streamlit Application Entry Point ---
def main():
    # If the user is not authenticated, show the login screen
    if not st.session_state.get(AUTH_STATUS_KEY):
        check_password()
    # If the user is authenticated, run the main app
    else:
        main_app()


if __name__ == "__main__":
    main()