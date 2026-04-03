import os
import zipfile
import sqlite3
import json
from google import genai  # Upgraded Library
from google.genai import types
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# --- 🧠 GEMINI 3.1 PRO CONFIGURATION ---
# The new SDK automatically looks for the GEMINI_API_KEY env var, 
# or we can set it explicitly here.
client = genai.Client(api_key="AIzaSyCPwXJN6vTTpXYez6lO-xNBtZqGg2-k0_8")
MODEL_ID = "gemini-3.1-pro" #

SYSTEM_PROMPT = """
You are the Pineapple Nutrition Brain, a biochemical nutritionist. 
Analyze the food data. Cross-reference NOVA (C7) with ingredients.
If a product is NOVA 4 but has simple ingredients (like Yogurt with pectin), re-evaluate.
Output ONLY a valid JSON object:
{
  "corrected_grade": "A-E",
  "narrative": "2-sentence warm explanation for a buddy.",
  "warning_flags": ["List specific harmful additives"],
  "healthier_alternative": "A generic suggestion"
}
"""

# --- 🚀 ENGINE ---
DB_FILE = "pineapple.db"
ZIP_FILE = "pineapple.zip"

if not os.path.exists(DB_FILE):
    if os.path.exists(ZIP_FILE):
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(".")

app = FastAPI(title="Pineapple AI Nutri-Scanner")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

async def analyze_with_gemini(product_data):
    """Uses the new Google GenAI SDK for Gemini 3.1 Pro analysis."""
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"{SYSTEM_PROMPT}\n\nDATA: {json.dumps(product_data)}"
        )
        # Strip markdown if present
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
def serve_webpage():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/scan/{barcode}")
async def scan_product(barcode: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE code = ?", (barcode,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    product_data = dict(row)
    ai_research = await analyze_with_gemini(product_data)
    
    if ai_research:
        product_data["ai_grade"] = ai_research.get("corrected_grade")
        product_data["ai_narrative"] = ai_research.get("narrative")
        product_data["ai_warnings"] = ai_research.get("warning_flags")
    
    return product_data

@app.get("/search/{query}")
def search(query: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT code, product_name, brands FROM products WHERE product_name LIKE ? LIMIT 10", (f"%{query}%",))
    rows = cursor.fetchall()
    conn.close()
    return {"results": [dict(row) for row in rows]}