import os
import zipfile
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# --- CONFIGURATION (Now Cloud-Ready & Relative) ---
DB_FILE = "pineapple.db"
ZIP_FILE = "pineapple.zip"

# --- 🚀 THE AUTO-UNZIPPER ---
# When Render starts up, it will check if the DB is unzipped.
# If it isn't, it unzips it silently in the background!
if not os.path.exists(DB_FILE):
    if os.path.exists(ZIP_FILE):
        print(f"📦 Extracting {ZIP_FILE}...")
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(".")
        print("✅ Extraction complete!")
    else:
        print("⚠️ WARNING: Neither pineapple.db nor pineapple.zip found!")

app = FastAPI(title="Pineapple Nutri-Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🌐 Serve the Frontend Webpage
@app.get("/", response_class=HTMLResponse)
def serve_webpage():
    """Serves the frontend index.html file to users."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: index.html not found.</h1><p>Make sure it is uploaded to GitHub!</p>"

# 🔍 Keyword Search (Finds products by Name or Brand, IGNORING GHOSTS)
@app.get("/search/{query}")
def search_by_name(query: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search for the query, but EXCLUDE ghosts (where ingredients are missing)
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT code, product_name, brands, C10_health_grade_alpha 
            FROM products 
            WHERE (product_name LIKE ? OR brands LIKE ?) 
            AND ingredients_text != 'nan' 
            AND "energy-kcal_100g" != 'nan'
            AND "energy-kcal_100g" != '0.0'
            LIMIT 15
        """, (search_term, search_term))
        
        rows = cursor.fetchall()
        conn.close()
        
        return {"results": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# 📷 Exact Barcode Scan
@app.get("/scan/{barcode}")
def scan_product(barcode: str):
    """Fetches the C1-C10 DNA for a scanned barcode."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE code = ?", (barcode,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        else:
            raise HTTPException(status_code=404, detail="Database error: 404: Product not found in database.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# 🛠️ Developer Tool
@app.get("/random")
def get_random_products():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT code, product_name, brands FROM products WHERE code IS NOT NULL LIMIT 3")
        rows = cursor.fetchall()
        conn.close()
        return {"test_products": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting the Pineapple Engine...")
    # 0.0.0.0 allows cloud platforms to route traffic to your app
    uvicorn.run(app, host="0.0.0.0", port=8000)