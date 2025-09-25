import os
from langchain_community.document_loaders import TextLoader
#from langchain_core.document_loaders import Document,TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
#from langchain_core.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables (for OpenAI API key)
load_dotenv()

# --- 1. Load the FAQ Document ---
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
loader = TextLoader(os.path.join(DATA_DIR, 'faq_document.txt'))
documents = loader.load()

# --- 2. Split the Document into Chunks ---
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

# --- 3. Create Embeddings and Vector Store ---
# This will use your OPENAI_API_KEY to create embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# Create a local FAISS vector store from the document chunks
# This process can take a moment as it calls the OpenAI API
print("---SERVICE: Creating FAISS vector store from FAQ document...---")
vector_store = FAISS.from_documents(chunks, embeddings)
print("---SERVICE: Vector store created successfully.---")

# --- 4. Create the RAG Chain ---
retriever = vector_store.as_retriever(search_kwargs={"k": 2}) # Retrieve top 2 chunks
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

template = """
You are a helpful assistant for our company's warranty support.
Answer the user's question based only on the following context.
If the context doesn't contain the answer, say you don't have enough information.

Context:
{context}

Question:
{question}
"""
prompt = ChatPromptTemplate.from_template(template)

# Create the RAG chain using LangChain Expression Language (LCEL)
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def query_faq_rag(question: str) -> str:
    """
    Queries the RAG system to get an answer for a general FAQ.
    """
    print(f"---SERVICE: Querying RAG for: '{question}'---")
    return rag_chain.invoke(question)