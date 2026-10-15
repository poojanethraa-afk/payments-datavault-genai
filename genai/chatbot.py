import os
from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from schema_docs import SCHEMA_DOCS

load_dotenv()

def build_retriever():
    docs=[Document(page_content=doc["description"], metadata={"table": doc["table"]})
          for doc in SCHEMA_DOCS]
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    vectorstore= FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})

if __name__ == "__main__":
    retriever = build_retriever()
    docs = retriever.invoke("Which customer paid the most in euro?")
    for d in docs:
        print(d.metadata["table"])