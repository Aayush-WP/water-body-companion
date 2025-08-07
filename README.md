# 🌊 Water Body Companion

A smart assistant that analyzes real-time data from Google Sheets and offers safety alerts, reports, and recommendations for water body management. Built using **Streamlit**, integrated with **Google Sheets** for live updates, and enhanced by **Gemini AI** for intelligent responses.

---

## 🚀 Features

- ✅ Live data fetching from Google Sheets
- ⚠️ Auto-generated alerts for serious or critical water issues
- 📊 Intelligent summaries & recommendations using Gemini AI
- 🔍 Searchable, filterable data interface
- 📱 Simple web interface powered by Streamlit
- 🔐 API keys are stored securely (not in codebase)

---

## 🌐 Live App

👉 [Click here to visit the app](https://water-body-companion.streamlit.app/)

---

## 🛠 How to Run the Project Locally

### 1. Clone the repository
git clone https://github.com/your-username/water-body-companion.git
cd water-body-companion

### 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Add your API keys and credentials
Create a .env file in the root directory with:
GEMINI_API_KEY=your_gemini_api_key

Save your Google Service Account JSON credentials as service_account.json (or any name you use in your code).
Make sure this file is in .gitignore to avoid uploading sensitive info.

### 5. Run the app
streamlit run main.py

## 🔌 APIs Used
Google Sheets API – For reading water data from Google Sheets

Google Drive API – (if applicable) for managing files and permissions

Google Generative AI (Gemini AI) – For generating smart alerts and insights

Streamlit – Web framework for interactive UI


