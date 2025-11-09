Multimodal Chatbot with Streamlit and MongoDB

A secure, full-featured **Multimodal Chatbot** application developed in Python using **Streamlit** for the frontend, **Google's Gemini API** for core AI intelligence, and **MongoDB Atlas** for secure user authentication.

---

✨ Features

* **Secure Authentication:** User login required before accessing the chat interface. Credentials are verified against a **MongoDB Atlas** collection using **SHA256 hashing** for passwords.
* **Multimodal AI:** Utilizes the **Gemini 2.5 Flash API** to handle both standard text conversations and analyze uploaded images (`.jpg`, `.png`).
* **Interactive UI:** Built entirely with **Streamlit** for a simple, responsive, and dynamic user experience.
* **Session Management:** Maintains chat history within the user's active session and allows users to clear the history or log out.
* **Configuration:** Uses the `dotenv` library to securely load API keys and database URIs from a `.env` file.

---

🛠️ Technologies Used

| Category | Technology | Dependency (for `requirements.txt`) |
| **App Framework** | **Streamlit** | `streamlit` |
| **AI Model** | **Google Gemini API** | `requests` |
| **Database** | **MongoDB Atlas** | `pymongo` |
| **Utilities** | **Python** | `python-dotenv`, `Pillow`, `hashlib` |

---

Getting Started

Follow these steps to set up and run the chatbot on your local machine.

Prerequisites

* **Python 3.8+**
* **Gemini API Key:** Obtain one from Google AI Studio.
* **MongoDB Atlas Cluster:** Set up a cluster and get the connection URI.

Installation and Setup

1.  **Clone the project** or create the files listed below.
2.  **Install dependencies** using the `requirements.txt` file:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file** and populate it using the `.env.example` template below.
4.  **Configure MongoDB:** Ensure your database (`sample_mflix`) and collection (`User_credentials`) are set up, and that user passwords are stored as **SHA256 hashes** in the `password_hash` field.

Running the App

1.  **Execute the Streamlit application:**

    ```bash
    streamlit run app.py
    ```

2.  The application will launch in your web browser (typically at `http://localhost:8501`).

---
🔒 Workflow
   
    Current Username : Anvit
    
    Password : a

1.  **Login Screen:** You must successfully log in using a registered username and password from your MongoDB collection.
2.  **Main Chat Interface:**
    * **Text Chat:** Type your prompt in the chat box at the bottom.
    * **Image Input:** Use the **`Upload File`** section in the sidebar to upload an image. Your next prompt will be sent along with the image for multimodal analysis.
3.  **Sidebar Controls:** Use **`Logout`** or **`Clear History`** buttons for session management.
