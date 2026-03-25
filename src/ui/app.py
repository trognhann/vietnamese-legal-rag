import streamlit as st

st.set_page_config(
    page_title="Vietnamese Legal Chatbot",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Vietnamese Legal RAG Q&A System")
st.markdown("---")
st.write("Welcome to the Vietnamese Legal Document Chatbot! Ask any legal questions below.")

# Initialize chat history if not present
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Nhập câu hỏi pháp lý của bạn tại đây..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # TODO: Connect to FastAPI backend here instead of dummy response
    response = f"Đây là câu trả lời mẫu cho câu hỏi: {prompt}"
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
