import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime

# ================= CONFIGURATION =================
GOOGLE_SHEET_NAME = "Water_Body_Form_Responses"
service_account_info = st.secrets["google_service_account"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SHEET_ID = "1UajWCygx78XEM6yyIxZsiMpC3HTgV7OjNb99bH8fGqk"

ADMIN_PASSWORDS = {
    "Delhi": "dlh_admin_123",
    "Noida": "nd_admin_456",
    "Mumbai": "mum_admin_789"
}

GENERAL_FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSdv9foMi-FDRfydeMw-MHzTtztvvrZcodjdcNUk3kX9uwk46w/viewform?usp=sharing"
ADMIN_FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSfyK49yrvtELhAekg4icrRzRhxOvBPbseH4iFsj89HP1VPpRQ/viewform?usp=sharing"

# =============== Gemini Setup ===============
genai.configure(api_key=GEMINI_API_KEY)

# =============== Google Sheet Fetch ===============
@st.cache_data(ttl=300)
def get_gsheet_data():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_info(dict(service_account_info), scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["Timestamp"])
        df["Date"] = df["Timestamp"].dt.date
    return df

# =============== Filter by today's date & area ===============
def filter_today_area_reports(df, area):
    today = datetime.today().date()
    area = area.lower()
    return df[(df["Date"] == today) & df.apply(lambda row: area in str(row).lower(), axis=1)]

# =============== Gemini Report Analyzer ===============
def analyze_reports_with_ai(reports_df):
    if reports_df.empty:
        return []
    report_text = reports_df.to_string(index=False)

    prompt = f"""
Analyze the following water body reports and highlight all serious ones.
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
    output = response.text.strip()

    serious_issues = []
    if "SERIOUS" in output.upper():
        issues = output.strip().split("Status: SERIOUS")
        for issue in issues[1:]:
            location = problem = reason = "N/A"
            for line in issue.strip().splitlines():
                if "Location:" in line:
                    location = line.split("Location:")[-1].strip()
                elif "Problem:" in line:
                    problem = line.split("Problem:")[-1].strip()
                elif "Reason:" in line:
                    reason = line.split("Reason:")[-1].strip()

            serious_issues.append({
                "location": location,
                "problem": problem,
                "reason": reason
            })
    return serious_issues

# =============== STREAMLIT UI ===============
st.set_page_config(page_title="Water Body Companion", layout="centered")
st.title("💧 Water Body Companion")

# Area selection & login
area = st.selectbox("Select your area:", list(ADMIN_PASSWORDS.keys()))
admin_password = st.text_input("Enter admin password for your area (leave blank for public access):", type="password")
is_admin = admin_password and ADMIN_PASSWORDS.get(area) == admin_password

df = get_gsheet_data()
today_area_df = filter_today_area_reports(df, area)

# 🔔 ALERT: Show serious issues for today in selected area
alerts = analyze_reports_with_ai(today_area_df)
if alerts:
    st.markdown("## 🔴 URGENT WATER ALERT (Today)")
    for alert in alerts:
        st.error(
            f"📍 Location: {alert['location']}\n\n"
            f"⚠ Problem: {alert['problem']}\n\n"
            f"🤖 AI Reason: {alert['reason']}"
        )

# =============== ADMIN PANEL ===============
if is_admin:
    st.success(f"🔑 Admin access granted for {area}")
    st.subheader("🔹 Admin Panel")
    st.markdown(f"[Open Admin Google Form]({ADMIN_FORM_LINK})")

    if st.button("View Today's Reports in This Area"):
        if today_area_df.empty:
            st.warning("⚠ No reports found for today in this area.")
        else:
            st.dataframe(today_area_df)

            st.info("⏳ Analyzing reports with AI...")
            ai_output = analyze_reports_with_ai(today_area_df)
            if ai_output:
                for issue in ai_output:
                    st.error("🔴 Serious Issue Detected!")
                    st.write(f"📍 Location: {issue['location']}")
                    st.write(f"⚠ Problem: {issue['problem']}")
                    st.write(f"🤖 AI Reason: {issue['reason']}")
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
