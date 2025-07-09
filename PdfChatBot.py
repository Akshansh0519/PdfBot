import os
import streamlit as st
import fitz  # PyMuPDF
from llama_index.core import Document
from llama_index.llms.gemini import Gemini
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
# Set Gemini API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAL98c1qUXkdf8ewPhL8mnyngmEVfV5ShQ"

# Configure LLM
llm = Gemini(model="models/gemini-1.5-pro-latest")
# PDF to text
def extract_text_from_pdf(file):
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text

# Ingest PDF and build index
def build_query_engine(text):
    # Wrap text as a document
    doc = Document(text=text)

    # Sentence splitter for chunking
    splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)
    nodes = splitter.get_nodes_from_documents([doc])

    # Use BM25 retriever instead of embedding search
    retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=5)

    

    # Create a response synthesizer using the LLM
    response_synthesizer = get_response_synthesizer(llm=llm)

    # Combine retriever and synthesizer
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer
    )
    return query_engine

# Streamlit UI
st.set_page_config(page_title="Gemini + LlamaIndex Chatbot")
st.title("📄 Chat with Your PDF")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
query_engine = None

if uploaded_file:
    # Check if this PDF has already been processed in the current session
    if "processed_pdf_name" not in st.session_state or st.session_state.processed_pdf_name != uploaded_file.name:
        st.session_state.messages = [] # Clear history for new PDF
        st.session_state.processed_pdf_name = uploaded_file.name
        with st.spinner("Reading and indexing PDF..."):
            text = extract_text_from_pdf(uploaded_file)
            st.session_state.query_engine = build_query_engine(text) # Store engine in session state
        st.success("PDF processed. You can now ask questions!")
    query_engine = st.session_state.query_engine # Retrieve engine for current session
else:
    # If no file is uploaded, but one was previously processed in this session
    if "query_engine" in st.session_state:
        query_engine = st.session_state.query_engine

if query_engine:
    user_query = st.chat_input("Ask a question about the PDF:") # Use st.chat_input
    if user_query:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.spinner("Generating answer..."):
            # If you want to include chat history in the LLM's context for multi-turn awareness,
            # you'd modify the query_engine call or prompt accordingly.
            # For a simple history display, just pass the current query.
            response = query_engine.query(user_query)

            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": response.response})
            with st.chat_message("assistant"):
                st.markdown(response.response)
