import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time

# ================= CONFIGURATION =================
GOOGLE_SHEET_NAME = "Water_Body_Form_Responses"
SERVICE_ACCOUNT_FILE = "service_account.json"  # Your service account file path
GEMINI_API_KEY = "AIzaSyCHFMGfIUYp98rwU_EcfyNf6BwXWQVw4VI"          # Your Gemini API key
SHEET_ID = "1UajWCygx78XEM6yyIxZsiMpC3HTgV7OjNb99bH8fGqk"  # Your Google Sheet ID

ADMIN_PASSWORDS = {
    "New York": "ny_admin_123",
    "Chicago": "chi_admin_456",
    "Mumbai": "mum_admin_789"
}

GENERAL_FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSdv9foMi-FDRfydeMw-MHzTtztvvrZcodjdcNUk3kX9uwk46w/viewform?usp=sharing&ouid=114749857380407029745"  # Replace with actual form link
ADMIN_FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSfyK49yrvtELhAekg4icrRzRhxOvBPbseH4iFsj89HP1VPpRQ/viewform?usp=sharing&ouid=114749857380407029745"      # Replace with actual form link

# =============== Gemini Setup ===============
genai.configure(api_key=GEMINI_API_KEY)

# =============== Google Sheet Fetch ===============
@st.cache_data
def get_gsheet_data():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# =============== Gemini Report Analyzer ===============
def analyze_reports_with_ai(reports_df):
    report_text = reports_df.to_string(index=False)

    prompt = f"""
Analyze the following water body reports and highlight only the serious ones.
For each serious issue, return in this format (plain text, no JSON):

Status: SERIOUS
Location: <Location>
Problem: <Problem description>
Reason: <Short reason>

If no serious issue is found, write:
Status: NOT SERIOUS

Reports:
{report_text}
"""

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text

# =============== Cache for Public Alert ===============
@st.cache_data(ttl=120)
def get_serious_issue_alert():
    df = get_gsheet_data()
    if df.empty:
        return None

    recent_df = df.tail(5)
    ai_output = analyze_reports_with_ai(recent_df)

    if "SERIOUS" in ai_output.upper():
        issues = ai_output.strip().split("Status: SERIOUS")
        if len(issues) > 1:
            issue = issues[2]
            location = problem = reason = "N/A"
            for line in issue.strip().splitlines():
                if "Location:" in line:
                    location = line.split("Location:")[-1].strip()
                elif "Problem:" in line:
                    problem = line.split("Problem:")[-1].strip()
                elif "Reason:" in line:
                    reason = line.split("Reason:")[-1].strip()

            return {
                "location": location,
                "problem": problem,
                "reason": reason
            }
    return None

# =============== STREAMLIT UI ===============
st.set_page_config(page_title="Water Body Companion", layout="centered")
st.title("💧 Water Body Companion")

# 🔔 ALERT: Show serious issue if found
alert = get_serious_issue_alert()
if alert:
    st.markdown("## 🔴 URGENT WATER ALERT")
    st.error(
        f"📍 Location: {alert['location']}\n\n"
        f"⚠ Problem: {alert['problem']}\n\n"
        f"🤖 AI Reason: {alert['reason']}"
    )

# Area selection & login
area = st.selectbox("Select your area:", list(ADMIN_PASSWORDS.keys()))
admin_password = st.text_input("Enter admin password for your area (leave blank for public access):", type="password")

is_admin = admin_password and ADMIN_PASSWORDS.get(area) == admin_password

# =============== ADMIN PANEL ===============
if is_admin:
    st.success(f"🔑 Admin access granted for {area}")

    st.subheader("🔹 Admin Panel")
    st.markdown(f"[Open Admin Google Form]({ADMIN_FORM_LINK})")

    if st.button("Fetch Latest Reports"):
        df = get_gsheet_data()

        if df.empty:
            st.warning("⚠ No data found yet")
        else:
            st.dataframe(df.tail(5))
            st.info("⏳ Analyzing reports with AI...")

            ai_output = analyze_reports_with_ai(df.tail(5))
            st.write("### AI Analysis Output:")
            #st.code(ai_output)

            if "SERIOUS" in ai_output.upper():
                issues = ai_output.strip().split("Status: SERIOUS")
                for issue in issues[1:]:  # skip first
                    location = problem = reason = "N/A"
                    for line in issue.strip().splitlines():
                        if "Location:" in line:
                            location = line.split("Location:")[-1].strip()
                        elif "Problem:" in line:
                            problem = line.split("Problem:")[-1].strip()
                        elif "Reason:" in line:
                            reason = line.split("Reason:")[-1].strip()

                    st.error("🔴 Serious Issue Detected!")
                    st.write(f"📍 Location: {location}")
                    st.write(f"⚠ Problem: {problem}")
                    st.write(f"🤖 AI Reason: {reason}")
            else:
                st.success("✅ No serious issues found.")

# =============== PUBLIC PANEL ===============
else:
    if admin_password:
        st.error("❌ Wrong admin password. Showing public user options.")

    st.subheader("🔹 General User Panel")
    st.markdown(f"[Submit Water Body Report]({GENERAL_FORM_LINK})")

    user_input = st.text_input("Ask the water body AI anything:")
    if st.button("Ask AI") and user_input.strip() != "":
        prompt = f"User query: {user_input}. Provide advice based on WHO water health guidance."
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        st.write("### AI Response:")
        st.write(response.text)