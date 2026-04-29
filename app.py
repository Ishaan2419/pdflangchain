import streamlit as st
import tempfile
import uuid

from service import create_db_from_uploaded, ask_question

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="Chat with PDFs")
st.header("📄 Chat with Multiple PDFs")

# -------------------------------
# Session
# -------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

session_id = st.session_state.session_id

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.subheader("Upload PDFs")

    pdf_docs = st.file_uploader(
        "Upload your PDFs",
        accept_multiple_files=True,
        type="pdf"
    )

    if st.button("Process"):
        if pdf_docs:
            file_paths = []

            for pdf in pdf_docs:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf.read())
                    file_paths.append(tmp.name)

            create_db_from_uploaded(file_paths)
            st.success("Done")

# -------------------------------
# Chat history
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------
# Chat input
# -------------------------------
if user_question := st.chat_input("Ask a question"):

    # user message
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # 🔥 FIX: direct call instead of API
    try:
        answer = ask_question(session_id, user_question)
    except Exception as e:
        answer = f"Error: {str(e)}"

    # assistant message
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
