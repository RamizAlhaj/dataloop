import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from fpdf import FPDF
import io
import datetime

st.set_page_config(page_title="Dataloop – Smart Report Generator", layout="wide")

# === Helper functions ===
def format_currency(x, pos):
    return f"₪{int(x):,}"

def generate_insights_v2(row):
    insights = []
    if row['Amount'] > 10000:
        insights.append("High revenue segment – monitor closely for trends.")
    if row['Amount'] < 2000:
        insights.append("Low activity – consider evaluating business need.")
    return " • ".join(insights) if insights else "Normal range performance."

def generate_pdf_v2(data):
    pdf = FPDF()
    pdf.add_page()

    # Cover Page
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Dataloop – Business Area Summary Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    today = datetime.date.today().strftime("%B %d, %Y")
    pdf.cell(0, 10, f"Date: {today}", ln=True, align='C')
    pdf.ln(10)

    # Summary Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Summary:", ln=True)
    pdf.set_font("Arial", '', 10)

    for _, row in data.iterrows():
        pdf.cell(0, 8, f"Business Area: {row['Business Area']}", ln=True)
        pdf.cell(0, 8, f"Date: {row['Date']} | Amount: ₪{int(row['Amount']):,}", ln=True)
        pdf.multi_cell(0, 8, f"Insights: {row['Insights']}", ln=True)
        pdf.ln(4)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# === Streamlit App ===
st.title("📊 Dataloop – Business Area Analyzer")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_cols = ['Business Area', 'Amount', 'Date', 'Year', 'Month', 'Day']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns in Excel file.")
    else:
        # Add insights
        df['Insights'] = df.apply(generate_insights_v2, axis=1)

        # Display table
        st.subheader("📋 Data Table")
        st.dataframe(df.style.format({
            'Amount': '₪{:,}'
        }))

        # Chart
        st.subheader("📈 Total Amount by Business Area")
        agg = df.groupby("Business Area")['Amount'].sum().reset_index()
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(agg['Business Area'], agg['Amount'], color='skyblue')
        ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
        plt.xticks(rotation=0)
        st.pyplot(fig)

        # PDF Export
        st.subheader("📄 Generate PDF")
        if st.button("Download PDF Report"):
            pdf_file = generate_pdf_v2(df)
            st.download_button("📥 Download Report", pdf_file, file_name="business_area_report.pdf", mime="application/pdf")
