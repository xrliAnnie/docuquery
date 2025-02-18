import streamlit as st
from services.api import APIClient

class ChatInterface:
    def __init__(self):
        self.api_client = APIClient()

    def __call__(self):
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about your document..."):
            if not st.session_state.current_document:
                st.warning("⚠️ Please upload a document first")
                return

            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Simulate AI response (replace with actual API call later)
            response = "This is a simulated response. The backend API is not connected yet."
            st.session_state.messages.append({"role": "assistant", "content": response})