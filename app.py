import streamlit as st
import requests
import json
import base64
import time
import io
from PIL import Image
import os
from dotenv import load_dotenv # ⬅️ NEW: Import load_dotenv

# --- Load Environment Variables ---
# This looks for a .env file and loads its contents into os.environ
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
# --- Configuration ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
SYSTEM_INSTRUCTION = "You are a friendly, helpful, and concise multimodal AI assistant. Provide detailed and accurate responses, especially when analyzing uploaded images."

# --- Helper Functions ---

def base64_encode_image(uploaded_file):
    """Encodes an uploaded Streamlit file to a base64 string and determines its mime type."""
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        encoded_string = base64.b64encode(file_bytes).decode('utf-8')
        return encoded_string, mime_type
    return None, None

def _get_gemini_response(api_key, chat_history, user_prompt, image_data=None, mime_type=None, max_retries=3):
    """
    Calls the API with the full chat history and handles multimodality.
    Implements exponential backoff for retries.
    """
    if not api_key:
        st.error("Error: Gemini API Key is not set in the environment variables.")
        return None

    # 1. Prepare chat contents
    contents = []
    for role, text in chat_history:
        contents.append({"role": role, "parts": [{"text": text}]})

    # 2. Add the user's new message and image (if available)
    user_parts = [{"text": user_prompt}]
    if image_data and mime_type:
        user_parts.insert(0, {
            "inlineData": {
                "mimeType": mime_type,
                "data": image_data
            }
        })
    contents.append({"role": "user", "parts": user_parts})

    # 3. Construct API payload
    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]}
    }

    headers = {'Content-Type': 'application/json'}
    
    # 4. API Call with Exponential Backoff
    for attempt in range(max_retries):
        try:
            with st.spinner("Generating response..."):
                response = requests.post(
                    f"{GEMINI_API_URL}?key={api_key}",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=60 # Set a reasonable timeout
                )
            
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
            
            result = response.json()
            
            # Extract generated text
            candidate = result.get("candidates", [{}])[0]
            if candidate and candidate.get("content", {}).get("parts", [{}])[0].get("text"):
                return candidate["content"]["parts"][0]["text"]
            else:
                return "Error: Could not extract text from the Gemini response."

        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.ConnectionError:
            st.error("Connection error. Check your network or API endpoint.")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                # st.warning(f"Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                st.error(f"Failed to connect to the API after {max_retries} attempts: {e}")
                return None
    return None

# --- Streamlit Application ---

def main():
    """Main function for the Streamlit application."""
    st.set_page_config(page_title="Multimodal Chatbot", layout="wide")
    st.title(" Ev Chatbot ")

    # --- Sidebar for Configuration ---
    with st.sidebar:
        st.header("Configuration")
        
        # Display key status instead of input
        if GEMINI_API_KEY:
             st.success("API Key loaded from **.env** file.")
        else:
             st.warning("⚠️ API Key not found. Please ensure the **.env** file is present and contains `GEMINI_API_KEY`.")

        # File Uploader
        st.subheader("Reference File (Optional)")
        uploaded_file = st.file_uploader(
            "Upload an image (JPG, PNG)", 
            type=["png", "jpg", "jpeg"],
            key="file_uploader"
        )
        
        # Display uploaded image preview
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image Preview", use_column_width=True)
            
        # Reset Button
        if st.button("Clear Chat History", key="clear_chat"):
            st.session_state.messages = []
            st.experimental_rerun()


    # --- Session State Initialization ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        initial_message = "Hello! I am a multimodal AI. Feel free to upload an image for analysis"
        if not GEMINI_API_KEY:
            initial_message += "\n\n**Note: The API Key is missing. Please check your `.env` file.**"
        
        st.session_state.messages.append(("model", initial_message))


    # --- Main Chat Interface ---

    # Display existing chat messages
    for role, text in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(text)

    # Handle user input
    if user_prompt := st.chat_input("Ask me anything...", disabled=not GEMINI_API_KEY):
        
        # Encode image if available
        image_data = None
        mime_type = None
        
        # Display user message with image if uploaded
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if uploaded_file:
                try:
                    # Open file stream to read the image for display
                    # Need to rewind the file object if it's already been read by Streamlit's internal processes
                    uploaded_file.seek(0) 
                    img = Image.open(uploaded_file)
                    st.image(img, caption='Reference Image', width=200)

                    # Encode for API call
                    uploaded_file.seek(0) # Rewind again for base64_encode_image
                    image_data, mime_type = base64_encode_image(uploaded_file)
                except Exception as e:
                    st.error(f"Could not process image: {e}")
            
        # Add user message to history
        st.session_state.messages.append(("user", user_prompt))

        # Prepare chat history for API (only text/image parts)
        api_history = [(r, t) for r, t in st.session_state.messages if r in ("user", "model")]
        
        # Get AI response
        ai_response = _get_gemini_response(GEMINI_API_KEY, api_history, user_prompt, image_data, mime_type)

        if ai_response:
            # Display AI response
            with st.chat_message("model"):
                st.markdown(ai_response)
            
            # Add AI response to history
            st.session_state.messages.append(("model", ai_response))


if __name__ == "__main__":
    main()