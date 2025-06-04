# Need to manage costs, but this is an example of how I could make AI a better research assistant
# Text extraction, chunking, embedding, and vector storage for a PDF document on Amazonian archaeology

import fitz  # PyMuPDF
from dotenv import load_dotenv
from openai import OpenAI

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

pdf_path = r"openai2z\docs\papers\A UAV lidar system to map Amazonian rainforest and its ancient landscape transformations.pdf"
output_txt_path = r"openai2z\docs\papers\lidar_amazon_text.txt"

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Extract pdf and save
text = extract_pdf_text(pdf_path)
with open(output_txt_path, "w", encoding="utf-8") as f:
    f.write(text)


load_dotenv()
client = OpenAI()

text_file_path = r"OpenAI2Z\openai2z\docs\papers\lidar_amazon_text.txt"
with open(text_file_path, "r", encoding="utf-8") as f:
    full_text = f.read()

# Split text from pdf into manageable chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_text(full_text)

# embed and store in FAISS vector DB
embedding_model = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(texts=chunks, embedding=embedding_model)

# saving the vectorstore locally
vectorstore.save_local("lidar_amazon_vectorstore")

print(f" Embedded {len(chunks)} text chunks and saved vector index.")

response = OpenAI().chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert in Amazonian archaeology."},
        {"role": "user", "content": f"Use the context below to answer the question:\n\n{context}\n\nQuestion: {query}"}
    ]
)

query = "What evidence is there for geometric earthworks in the Amazon basin? Please list features and their locations."

relevant_docs = vectorstore.similarity_search(query, k=3)
context = "\n\n".join([doc.page_content for doc in relevant_docs])

print(response.choices[0].message.content)