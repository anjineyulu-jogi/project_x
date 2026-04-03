import os
import zipfile
import sqlite3
import json
from google import genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# --- 🧠 GEMINI 3 PRO CONFIGURATION (SECURE) ---
# Pulled from Render Environment Variables to prevent vulnerabilities
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-3-pro" # Upgraded to 3 Pro

SYSTEM_PROMPT = """
You are the Pineapple Nutrition Brain. 
Analyze the food data. Cross-reference NOVA (C7) with ingredients.
If a product is NOVA 4 but has simple ingredients (like Yogurt with pectin), re-evaluate.
Output ONLY a valid JSON object:
{
  "corrected_grade": "A-E",
  "narrative": "Provide a 2-sentence warm, helpful explanation for a friend.",
  "warning_flags": ["List harmful additives"],
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

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

async def analyze_with_gemini(product_data):
    """Uses Gemini 3 Pro to generate real summaries."""
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"{SYSTEM_PROMPT}\n\nDATA: {json.dumps(product_data)}"
        )
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
    # Fixed: Now selecting the health grade to show in search results
    cursor.execute("""
        SELECT code, product_name, brands, C10_health_grade_alpha 
        FROM products 
        WHERE product_name LIKE ? 
        LIMIT 15
    """, (f"%{query}%",))
    rows = cursor.fetchall()
    conn.close()
    return {"results": [dict(row) for row in rows]}