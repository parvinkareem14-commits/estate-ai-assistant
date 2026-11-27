
import os
import json
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "chats.json"

st.set_page_config(
    page_title="Estate AI",
    page_icon="🏠",
    layout="wide"
)

# Load Groq API key
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY missing. Check your .env file.")
    st.stop()

client = Groq(api_key=api_key)


# Load saved chats
def load_chats():
    try:
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        st.error("Unable to read chats.json.")
    return {}


# Save chats permanently
def save_chats():
    temp_file = DATA_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(
            st.session_state.chats,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )
    temp_file.replace(DATA_FILE)


# Create a new chat
def create_new_chat():
    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": []
    }

    st.session_state.active_chat_id = chat_id
    save_chats()


# Initialize session
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "active_chat_id" not in st.session_state:
    if st.session_state.chats:
        st.session_state.active_chat_id = list(
            st.session_state.chats.keys()
        )[-1]
    else:
        create_new_chat()


# Sidebar
with st.sidebar:

    st.title("🏠 Estate AI")

    if st.button("＋ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()

    st.subheader("Recent Chats")

    for chat_id in reversed(list(st.session_state.chats.keys())):

        chat = st.session_state.chats[chat_id]

        title = chat.get("title", "New Chat")

        if st.button(
            "💬 " + title[:35],
            key=f"chat_{chat_id}",
            use_container_width=True
        ):
            st.session_state.active_chat_id = chat_id
            st.rerun()


# Current chat
active_id = st.session_state.active_chat_id
current_chat = st.session_state.chats[active_id]
messages = current_chat["messages"]


# Main Chat UI
st.title("Estate AI")
st.caption("Your Real Estate AI Assistant")


# Display conversation history
for message in messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# User input
prompt = st.chat_input("Ask your real estate question...")

if prompt:

    # Create title from first question
    if not messages:
        current_chat["title"] = prompt[:35]

    # Save user message
    messages.append({
        "role": "user",
        "content": prompt
    })

    save_chats()

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Estate AI is thinking..."):

            try:

                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are Estate AI, a helpful real estate "
                                "assistant. Answer questions about buying, "
                                "selling, renting and property investment "
                                "in simple and clear language."
                            )
                        }
                    ] + messages,
                    max_completion_tokens=800
                )

                answer = response.choices[0].message.content

                st.markdown(answer)

                messages.append({
                    "role": "assistant",
                    "content": answer
                })

                save_chats()

            except Exception as e:
                st.error(f"Groq API Error: {e}")
