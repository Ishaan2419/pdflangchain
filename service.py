import os

from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.documents import Document

from PyPDF2 import PdfReader


# -------------------------------
# load single pdf
# -------------------------------
def get_load_pdf(file_path):
    doc = []
    reader = PdfReader(file_path)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()

        if text:
            doc.append(
                Document(
                    page_content=text,
                    metadata={"source": file_path, "page": i + 1}
                )
            )
    return doc


# -------------------------------
# load multiple pdf
# -------------------------------
def load_multiple_pdf(file_list):
    docs = []
    for file in file_list:
        docs.extend(get_load_pdf(file))
    return docs


# -------------------------------
# chunking
# -------------------------------
def splitt(doc):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    return splitter.split_documents(doc)


# -------------------------------
# create db
# -------------------------------
def create_db(chunk):
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma.from_documents(
        documents=chunk,
        embedding=embedding,
        persist_directory="cc"
    )

    return db


# -------------------------------
# create db from uploaded pdfs
# -------------------------------
def create_db_from_uploaded(files):
    docs = load_multiple_pdf(files)
    chunks = splitt(docs)
    return create_db(chunks)


# -------------------------------
# load db
# -------------------------------
def load_db():
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory="cc",
        embedding_function=embedding,
    )

    return db


# -------------------------------
# init db
# -------------------------------
def init_db():
    if os.path.exists("cc"):
        return load_db()
    else:
        return None


db = init_db()


# -------------------------------
# LLM
# -------------------------------
llm = ChatOllama(model="phi:mini")


# -------------------------------
# Memory
# -------------------------------
store = {}

def get_session_id(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# -------------------------------
# prompt
# -------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant.
    Rules:
    1. If the question is about previous conversation, answer ONLY from chat history.
    2. If the question is about document content, use the provided context.
    3. If both are relevant, use both.
    4. Never ignore chat history when user asks about past messages.
    5. If answer not in context → say "I don't know".
    6. Answer in 1-2 lines only.
    7. Be direct and concise.
    """),
    MessagesPlaceholder(variable_name="history"),
    ("human", "context:\n\n{context}\n\nQuestion:{input}")
])


# -------------------------------
# chain
# -------------------------------
chain = prompt | llm

chat = RunnableWithMessageHistory(
    chain,
    get_session_id,
    input_messages_key="input",
    history_messages_key="history"
)


# -------------------------------
# ask question
# -------------------------------
def ask_question(session_id, query):
    history_keywords = ["previous", "last question", "what did i ask", "history"]

    if any(word in query.lower() for word in history_keywords):
        context = ""
    else:
        if db is None:
            context = ""
        else:
            retriever = db.as_retriever()
            docs = retriever.invoke(query)
            context = "\n\n".join(d.page_content for d in docs)

    response = chat.invoke(
        {
            "input": query,
            "context": context
        },
        config={"configurable": {"session_id": session_id}}
    )

    return response.content.split("Answer:")[-1].replace("\n", " ").strip()
