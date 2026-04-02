# 🍍 Pineapple Nutri-Scanner (MVP)

  An intelligent, accessible web application designed to scan food barcodes and provide instantaneous, human-readable health grades.

## 🚀 Features
* **Omni-Channel Search:** Scan physical barcodes via the device camera or manually search by product/brand name.
* **The Intelligence Layer:** Calculates a custom Health Grade (A-E) using a proprietary algorithm that cross-references NOVA processing grades, HFSS (High Fat/Sugar/Salt) flags, and dietary compliance (like Jain indexing).
* **Ghost Protocol:** Automatically detects and filters out "Ghost" products that have missing nutritional data to prevent false-positive grades.
* **Built for Accessibility:** Features a modern Glassmorphism UI and a hidden `aria-live` region that automatically reads the AI narrative summary out loud for visually impaired users via TalkBack.

## 🛠️ Tech Stack
* **Backend:** Python, FastAPI, SQLite
* **Frontend:** HTML5, Vanilla JavaScript, CSS3
* **Scanner:** html5-qrcode library
