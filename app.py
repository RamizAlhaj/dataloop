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

def generate_insights(row):
    insights = []
    if row['Cost %'] > 60:
        insights.append("High cost ratio. Consider reviewing suppliers or pricing strategy.")
    if row['Productivity'] < 100:
        insights.append("Low productivity. Consider optimizing staff shifts.")
    if row['Customer Satisfaction'] < 4:
        insights.append("Customer satisfaction is below average. Consider improving service quality.")
    if not insights:
        insights.append("Performance is within expected range.")
    return " • ".join(insights)

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()

    # Cover Page
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Dataloop – Smart Monthly Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    today = datetime.date.today().strftime("%B %d, %Y")
    pdf.cell(0, 10, f"Date: {today}", ln=True, align='C')
    pdf.ln(10)

    # Summary Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Summary:", ln=True)
    pdf.set_font("Arial", '', 10)

    for _, row in data.iterrows():
        pdf.cell(0, 8, f"Section: {row['Restaurant/Section']}", ln=True)
        pdf.cell(0, 8, f"Month: {row['Month']} | Sales: ₪{int(row['Sales']):,} | Costs: ₪{int(row['Costs']):,} | Net Profit: ₪{int(row['Net Profit']):,}", ln=True)
        pdf.cell(0, 8, f"Cost %: {row['Cost %']:.1f}% | Productivity: {row['Productivity']:.1f} | Satisfaction: {row['Customer Satisfaction']:.1f}", ln=True)
        pdf.multi_cell(0, 8, f"Insights: {row['Insights']}", ln=True)
        pdf.ln(4)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# === Streamlit App ===
st.title("📊 Dataloop – Smart Report Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_cols = ['Restaurant/Section', 'Month', 'Sales', 'Costs', 'Employees', 'Orders', 'Waste (%)', 'Customer Satisfaction']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns in Excel file.")
    else:
        # Calculations
        df['Net Profit'] = df['Sales'] - df['Costs']
        df['Cost %'] = (df['Costs'] / df['Sales']) * 100
        df['Productivity'] = df['Orders'] / df['Employees']
        df['Insights'] = df.apply(generate_insights, axis=1)

        # Display table
        st.subheader("📋 Report Table")
        st.dataframe(df.style.format({
            'Sales': '₪{:,}', 'Costs': '₪{:,}', 'Net Profit': '₪{:,}',
            'Cost %': '{:.1f}%', 'Productivity': '{:.1f}', 'Customer Satisfaction': '{:.1f}'
        }))

        # Chart
        st.subheader("📈 Performance Comparison")
        fig, ax = plt.subplots(figsize=(10, 5))
        df.plot(x='Restaurant/Section', y=['Sales', 'Costs', 'Net Profit'], kind='bar', ax=ax)
        ax.yaxis.set_major_formatter(FuncFormatter(format_currency))
        plt.xticks(rotation=0)
        st.pyplot(fig)

        # PDF Export
        st.subheader("📄 Generate PDF")
        if st.button("Download PDF Report"):
            pdf_file = generate_pdf(df)
            st.download_button("📥 Download Report", pdf_file, file_name="dataloop_report.pdf", mime="application/pdf")
