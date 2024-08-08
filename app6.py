from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai
from groq import Groq
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

# Configure generative AI with Google API key
api_key = os.getenv("GOOGLE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("No API key found. Please set the GOOGLE_API_KEY environment variable.")
else:
    genai.configure(api_key=api_key)

# Predefined questions and answers
predefined_qna = {
    "who are you": "I am Lighthouse Info Systems Pvt. Ltd., a leading provider of ERP solutions for various industries. A multimodal AI model developed by LHS.",
    "who made you": "I was created by the team at LHS."
}

# Function to load Gemini Pro model and start chat
def start_chat():
    return genai.GenerativeModel("gemini-pro").start_chat(history=[])

def get_gemini_response(chat, question):
    response = chat.send_message(question, stream=True)
    response_text = ""
    for chunk in response:
        response_text += chunk.text
    return response_text

# Groq API class
class GroqAPI:
    """Handles API operations with Groq to generate chat responses."""
    def __init__(self, model_name: str):
        self.client = Groq(api_key=groq_api_key)
        self.model_name = model_name

    def _response(self, messages):
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0,
            stream=True,
            stop=None,
        )

    def response_stream(self, messages):
        for chunk in self._response(messages):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

# Function to get Groq response
groq_model = GroqAPI("llama-3.1-70b-versatile")
def get_groq_response(messages):
    response = groq_model.response_stream(messages)
    response_text = ""
    for chunk in response:
        response_text += chunk
    return response_text

# Function to replace "Gemini" or "Google" with "Lighthouse" and "LHS" in responses
def replace_lighthouse_terms(response):
    response = response.replace("Gemini", "LHS-BOT")
    response = response.replace("Google", "Lighthouse Info Systems Pvt. Ltd.")
    return response

# Set page configuration and title
st.set_page_config(page_title="Lighthouse GPT", layout="wide", initial_sidebar_state="expanded")

# Initialize session state if not already done
if 'chat' not in st.session_state:
    st.session_state['chat'] = start_chat()
if 'conversations' not in st.session_state:
    st.session_state['conversations'] = []
if 'selected_conversation' not in st.session_state:
    st.session_state['selected_conversation'] = None
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = 'Gemini'
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Function to clear session state
def clear_conversations():
    st.session_state['conversations'] = []
    st.session_state['selected_conversation'] = None
    st.session_state['chat'] = start_chat()
    st.session_state['chat_history'] = []

# Custom CSS for styling
st.markdown("""
    <style>
        .fixed-header {
            position: fixed;
            top: 0;
            width: 75%;
            height: 150px;
            background-color: #fff; /* Change to desired background color */
            z-index: 1000;
            display: flex;
            align-items: center;
            padding: 70px 40px 20px 25px;
            color: #fff; /* Change to desired text color */
            margin-right: 50px;
        }
        .fixed-text-header {
            padding: 25px 80px 20px 50px;; /* Adjust this value based on your preference */
            color: #fff; /* Change to desired text color */
        }
        .main-content {
            margin-top: 40px; /* Adjust this value based on the height of your header */
            padding: 5px;
        }
        .fixed-top-left {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 9999;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
        }
        .sidebar-content {
            margin-top: 60px;
        }
        .sidebar-history {
            margin-top: 20px;
        }           
        #MainMenu{
            display:none;
        }
        .stActionButton{
            display:none;
        }
    </style>
""", unsafe_allow_html=True)

# Updated HTML for the fixed header
st.markdown("""
    <div class="fixed-header">
    <img src="https://www.lighthouseindia.com/images/slider2020/lhs-logo.webp " alt="Logo" style="height: 70px; margin-right: 10px; margin-top:6px;>
        <div class="fixed-text-header">
            <h1>Lighthouse GPT</h1>
        </div>
    </div>
""", unsafe_allow_html=True)


# Sidebar for displaying prompts and model selection
with st.sidebar:
    # Fixed position model selection with radio buttons
    st.markdown('<div class="fixed-top-left">', unsafe_allow_html=True)
    selected_model = st.radio(label="Select Model", options=["Gemini", "Groq:llama-3.1"], key="model_selector")
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state['selected_model'] = selected_model
    
    st.header("Session History")

    # Button to clear all conversations
    if st.button("Clear All Conversations", key="clear_button"):
        clear_conversations()

    st.markdown('<div class="sidebar-history">', unsafe_allow_html=True)

    # Display prompts and handle click events
    for idx, convo in enumerate(st.session_state['conversations']):
        if st.button(convo['prompt'], key=idx):
            st.session_state['selected_conversation'] = idx

    st.markdown('</div>', unsafe_allow_html=True)


# Main content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Supervise user input
if user_input := st.chat_input("Message Lighthouse GPT..."):
    # Append user input to history
    st.session_state['chat_history'].append({"role": "user", "content": user_input})
    
    # Create a conversation object
    conversation = {"prompt": user_input, "history": [("You", user_input)]}

    # Check if user input matches any predefined question
    if user_input.lower() in predefined_qna:
        response_text = predefined_qna[user_input.lower()]
        conversation['history'].append(("Bot", response_text))
        st.session_state['chat_history'].append({"role": "assistant", "content": response_text})
    else:
        # Get response from the selected model
        if st.session_state['selected_model'] == "Gemini":
            chat = st.session_state['chat']
            response_text = get_gemini_response(chat, user_input)
        else:
            response_text = get_groq_response(st.session_state['chat_history'] + [{"role": "user", "content": user_input}])

        response_text = replace_lighthouse_terms(response_text)
        conversation['history'].append(("Bot", response_text))
        
        # Update chat history
        st.session_state['chat_history'].append({"role": "assistant", "content": response_text})

    # Update session state and selected conversation
    st.session_state['conversations'].append(conversation)
    st.session_state['selected_conversation'] = len(st.session_state['conversations']) - 1

# Display selected conversation
if st.session_state['selected_conversation'] is not None:
    selected_conversation = st.session_state['conversations'][st.session_state['selected_conversation']]
    for role, text in selected_conversation['history']:
        st.markdown(f"**{role}**: {text}")

st.markdown('</div>', unsafe_allow_html=True)

# Script to enable pressing enter to send message
st.markdown("""
<script>
const inputBox = document.querySelector('textarea[aria-label="Message LHS GPT..."]');
inputBox.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        inputBox.value += '\\n';
    }
});
</script>
""", unsafe_allow_html=True)
