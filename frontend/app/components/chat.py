import streamlit as st
from services.api import APIClient

class ChatInterface:
    def __init__(self):
        self.api_client = APIClient()

    def __call__(self):
        if not st.session_state.current_document:
            return

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message:
                    with st.expander("View Sources"):
                        for source in message["sources"]:
                            st.markdown(f"📄 Page {source['page']}: {source['text']}")

        # Chat input
        if prompt := st.chat_input("Ask a question about your document..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get AI response from backend
            with st.spinner("Thinking..."):
                response = self.api_client.query_document(
                    st.session_state.current_document,
                    prompt
                )
                
                if response.get("status") != "error":
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response.get("sources", [])
                    })
                else:
                    st.error(f"❌ Error: {response.get('message')}")