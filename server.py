import os
import zipfile
import sqlite3
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# --- 🧠 GEMINI AI CONFIGURATION ---
# Using the key you provided and the latest Gemini 3.1 Pro flagship model
genai.configure(api_key="AIzaSyCPwXJN6vTTpXYez6lO-xNBtZqGg2-k0_8")
model = genai.GenerativeModel('gemini-3.1-pro') 

SYSTEM_PROMPT = """
You are the Pineapple Nutrition Brain, a biochemical nutritionist. 
Analyze the provided JSON food data. Cross-reference NOVA processing (C7) with ingredients.
If a product is NOVA 4 but has simple ingredients (like Yogurt with pectin), re-evaluate the grade.
Check Jain compliance (C4) against the ingredients list.
Output ONLY a valid JSON object with:
{
  "corrected_grade": "A-E",
  "narrative": "2-sentence warm explanation for a buddy.",
  "warning_flags": ["List specific harmful additives"],
  "healthier_alternative": "A generic suggestion"
}
"""

# --- 🚀 THE DATABASE ENGINE ---
DB_FILE = "pineapple.db"
ZIP_FILE = "pineapple.zip"

if not os.path.exists(DB_FILE):
    if os.path.exists(ZIP_FILE):
        print(f"📦 Extracting {ZIP_FILE}...")
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(".")
        print("✅ Extraction complete!")

app = FastAPI(title="Pineapple AI Nutri-Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🤖 THE AI ANALYSIS LAYER ---
async def analyze_with_gemini(product_data):
    """Sends raw DB data to Gemini 3.1 Pro for deep biochemical research."""
    try:
        combined_input = f"{SYSTEM_PROMPT}\n\nDATA:\n{json.dumps(product_data)}"
        response = model.generate_content(combined_input)
        
        # 🧼 CLEANING THE AI RESPONSE 
        # Gemini 3.1 often wraps JSON in markdown blocks; we strip those out.
        clean_json = response.text
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0]
            
        return json.loads(clean_json.strip())
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# --- 🌐 ROUTES ---

@app.get("/", response_class=HTMLResponse)
def serve_webpage():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: index.html not found.</h1>"

@app.get("/scan/{barcode}")
async def scan_product(barcode: str):
    """Fetches DNA from DB, then passes it through the Gemini 3.1 Pro Brain."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE code = ?", (barcode,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Product not in database.")

        product_data = dict(row)
        
        # ⚡️ ACTIVATE GEMINI 3.1 PRO RESEARCH ⚡️
        ai_research = await analyze_with_gemini(product_data)
        
        # Merge AI insights into the original data
        if ai_research:
            product_data["ai_grade"] = ai_research.get("corrected_grade")
            product_data["ai_narrative"] = ai_research.get("narrative")
            product_data["ai_warnings"] = ai_research.get("warning_flags")
            product_data["ai_alt"] = ai_research.get("healthier_alternative")
            
        return product_data
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/{query}")
def search_by_name(query: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    search_term = f"%{query}%"
    cursor.execute("""
        SELECT code, product_name, brands, C10_health_grade_alpha 
        FROM products 
        WHERE (product_name LIKE ? OR brands LIKE ?) 
        AND ingredients_text != 'nan' 
        LIMIT 15
    """, (search_term, search_term))
    rows = cursor.fetchall()
    conn.close()
    return {"results": [dict(row) for row in rows]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)