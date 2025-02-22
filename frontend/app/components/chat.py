import streamlit as st
from services.api import APIClient
import requests
import logging

# Configure logging (you can later adjust this configuration as needed)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatInterface:
    def __init__(self):
        logger.debug("Initializing ChatInterface...")
        self.api_client = APIClient()
        logger.debug("APIClient initialized.")

    def __call__(self):
        logger.debug("ChatInterface __call__ invoked.")
        logger.debug(f"Session state keys before checking document: {list(st.session_state.keys())}")

        logger.debug(f"current_document value: {st.session_state.get('current_document')}")
        if not st.session_state.get("current_document"):
            logger.debug("No document found in session state. Exiting chat interface rendering.")
            return
        else:
            logger.debug("Found a document in session state; proceeding with chat interface.")

        # Display chat history
        if "messages" in st.session_state:
            logger.debug(f"Rendering {len(st.session_state.messages)} chat messages.")
            for idx, message in enumerate(st.session_state.messages):
                logger.debug(f"Rendering message {idx}: role={message.get('role')}, content={message.get('content')[:50]}")
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "sources" in message:
                        with st.expander("View Sources"):
                            for source in message["sources"]:
                                logger.debug(f"Rendering source: Page {source.get('page')}, text snippet: {source.get('text')[:50]}")
                                st.markdown(f"📄 Page {source['page']}: {source['text']}")
        else:
            logger.debug("No messages found in session state.")

        # Chat input
        logger.debug("Displaying chat input box.")
        user_input = st.chat_input("Ask a question about your document...")
        if user_input:
            logger.debug(f"User input received: {user_input}")
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            logger.debug("User message appended to session state.")

            # Get AI response from backend
            with st.spinner("Thinking..."):
                logger.debug("Calling APIClient.query_document...")
                response = self.api_client.query_document(
                    st.session_state.current_document,
                    user_input
                )
                logger.debug(f"Received response from APIClient: {response}")

                if response.get("status") != "error":
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response.get("sources", [])
                    })
                    logger.debug("Assistant message appended to session state.")
                else:
                    st.error(f"❌ Error: {response.get('message')}")
                    logger.error(f"Error processing query: {response.get('message')}")

    def ask_question(self):
        logger.debug("ChatInterface.ask_question invoked.")
        st.header("Ask a Question")
        logger.debug("Header rendered for ask_question.")
        st.write("Debug: ChatInterface is active.")
        logger.debug("Debug text rendered.")

        # Text input for the question
        question = st.text_input("Enter your question here:")
        if question:
            logger.debug(f"User question input: {question}")

        # When the user clicks the submit button:
        if st.button("Submit"):
            logger.debug("Submit button clicked in ask_question.")
            if not question or not question.strip():
                st.error("Please enter a valid question.")
                logger.error("No question provided by the user.")
            else:
                try:
                    logger.debug("Sending POST request to backend query endpoint.")
                    # Ensure the payload is properly structured
                    payload = {
                        "text": question.strip(),
                        "filters": {}
                    }
                    logger.debug(f"Request payload: {payload}")
                    
                    response = requests.post(
                        "http://localhost:8001/api/v1/query",
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                    )
                    logger.debug(f"Backend response status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        logger.debug(f"Response JSON: {data}")
                        answer = data.get("answer", "No answer returned")
                        st.write("**Answer:**", answer)
                    else:
                        st.error(f"Error from backend: {response.text}")
                        logger.error(f"Error from backend: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to backend: {str(e)}")
                    logger.exception("Exception while sending query to backend.")

if __name__ == "__main__":
    logger.debug("Starting ChatInterface application...")
    chat_interface = ChatInterface()
    chat_interface()  # Call the instance to render the chat interface
