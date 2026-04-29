import streamlit as st
import requests
import tempfile
import uuid

from service import create_db_from_uploaded

st.set_page_config(page_title="Chat with PDFs")
st.header("📄 Chat with Multiple PDFs")

# -------------------------------
# session
# -------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

session_id = st.session_state.session_id

# -------------------------------
# sidebar
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
# chat history
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------
# chat input
# -------------------------------
if user_question := st.chat_input("Ask a question"):

    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={
            "session_id": session_id,
            "query": user_question
        }
    )

    answer = response.json()["Answer"]

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
