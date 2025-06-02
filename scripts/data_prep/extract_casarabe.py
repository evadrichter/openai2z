import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

import pandas as pd
from docx import Document
from io import StringIO

# OpenAI Environment Setup
load_dotenv()
client = OpenAI()
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("No OPENAI_API_KEY in .env")

#all config paths
GITHUB_DOC_URL = "https://raw.githubusercontent.com/evadrichter/openai2z/main/docs/resources/41586_2022_4780_MOESM1_ESM.docx"
EXPECTED_COLUMNS = ["site_name", "utm_x", "utm_y", "tier"]
LOCAL_DOCX = "temp_download.docx"

#define prompt path: 
base_dir = os.path.dirname(__file__)  
PROMPT_PATH = Path(os.path.join(base_dir, "openai2z\prompts\extract_casarabe.txt"))

# all helper functions
def download_docx(url, save_path):
    save_path = Path(save_path)  # ensure it's a Path object
    response = requests.get(url)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(response.content)
    if not save_path.exists():
        raise FileNotFoundError(f"Expected file at {save_path} not found after download.")
    return save_path


def extract_text_from_docx(path):
    if not path.exists():
        raise FileNotFoundError(f"Cannot extract text: file not found at {path}")
    doc = Document(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

def load_prompt(prompt_path):
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()

def gpt_extract_sites(prompt_base, doc_text):
    truncated_text = doc_text[:8000]
    user_prompt = f"{prompt_base}\n\nText:\n{truncated_text}"
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert in archaeological data extraction."},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )
    return completion.choices[0].message.content.strip()

def parse_csv_output(csv_text):
    try:
        df = pd.read_csv(StringIO(csv_text))
        return df
    except Exception as e:
        print(f"Failed to parse GPT output as CSV: {e}")
        return pd.DataFrame()

def validate_site_data(df):
    if not all(col in df.columns for col in EXPECTED_COLUMNS):
        print("Missing one or more expected columns.")
        return pd.DataFrame()

    for col in ["utm_x", "utm_y"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["utm_x", "utm_y"])
    df["tier"] = df["tier"].astype(str).str.extract(r"(\d+)", expand=False)
    df["tier"] = pd.to_numeric(df["tier"], errors="coerce").fillna(0).astype(int)
    return df

#main orchestration:
def extract_casarabe_sites():
    print("Downloading DOCX from GitHub...")
    docx_path = download_docx(GITHUB_DOC_URL, LOCAL_DOCX)

    print("Extracting text from document...")
    text = extract_text_from_docx(docx_path)

    print("Loading structured prompt...")
    prompt_text = load_prompt(PROMPT_PATH)

    print("Sending document to GPT...")
    csv_response = gpt_extract_sites(prompt_text, text)

    print("Parsing response...")
    df = parse_csv_output(csv_response)

    print("Validating fields...")
    df_clean = validate_site_data(df)

    if not df_clean.empty:
        df_clean.to_csv("casarabe_sites_clean.csv", index=False)
        print("Saved cleaned site data to casarabe_sites_clean.csv")
    else:
        print("No valid data extracted.")

    return df_clean


if __name__ == "__main__":
    extract_casarabe_sites()
