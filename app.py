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
        insights.append("High revenue segment")
    if row['Amount'] < 2000:
        insights.append("Low activity")
    if row['Day'] in [5, 6]:
        insights.append("Weekend trend")
    if row['Month'] in [1, 8, 12]:
        insights.append("Holiday month")
    return " | ".join(insights) if insights else "Normal"

def generate_pdf_v2(data, summary_df, top_bottom_df, area_perf):
    pdf = FPDF()
    pdf.add_page()

    # Use basic core font
    pdf.set_font("Arial", '', 12)

    # Cover Page
    pdf.cell(0, 10, "Dataloop – Business Area Summary Report", ln=True, align='C')
    today = datetime.date.today().strftime("%B %d, %Y")
    pdf.cell(0, 10, f"Date: {today}", ln=True, align='C')
    pdf.ln(10)

    # Summary Table
    pdf.cell(0, 10, "Monthly Summary by Business Area:", ln=True)
    for _, row in summary_df.iterrows():
        pdf.cell(0, 8, f"{row['Business Area']} ({row['Month']}): {int(row['Amount']):,} NIS", ln=True)
    pdf.ln(8)

    # Top and Bottom
    pdf.cell(0, 10, "Top & Bottom Performers:", ln=True)
    for _, row in top_bottom_df.iterrows():
        pdf.cell(0, 8, f"{row['Label']}: {row['Business Area']} – {int(row['Amount']):,} NIS", ln=True)
    pdf.ln(8)

    # Scores & Recommendations
    pdf.cell(0, 10, "Performance Scores & Action Items:", ln=True)
    for area, row in area_perf.iterrows():
        score = row['Score']
        msg = f"{area}: Score {score}/10. "
        if score < 5:
            msg += "Performance review recommended."
        elif score > 8:
            msg += "Strong – consider promotion."
        else:
            msg += "Stable."
        pdf.multi_cell(0, 8, msg)
    pdf.ln(8)

    # Detailed Records
    pdf.cell(0, 10, "Detailed Records:", ln=True)
    for _, row in data.iterrows():
        pdf.cell(0, 8, f"Business Area: {row['Business Area']}", ln=True)
        pdf.cell(0, 8, f"Date: {row['Date']} | Amount: {int(row['Amount']):,} NIS", ln=True)
        pdf.multi_cell(0, 8, f"Insights: {row['Insights']}")
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
        df['Insights'] = df.apply(generate_insights_v2, axis=1)
        df['Date'] = pd.to_datetime(df['Date'])
        df['Weekday'] = df['Date'].dt.day_name()

        st.subheader("📋 Data Table")
        st.dataframe(df.style.format({'Amount': '₪{:,}'}))

        st.subheader("📈 Total Amount by Business Area")
        agg = df.groupby("Business Area")['Amount'].sum().reset_index()
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.bar(agg['Business Area'], agg['Amount'], color='skyblue')
        ax1.yaxis.set_major_formatter(FuncFormatter(format_currency))
        plt.xticks(rotation=0)
        st.pyplot(fig1)

        st.subheader("📋 Monthly Trend by Business Area")
        monthly = df.groupby(['Month', 'Business Area'])['Amount'].sum().reset_index()
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        for area in monthly['Business Area'].unique():
            area_data = monthly[monthly['Business Area'] == area]
            ax2.plot(area_data['Month'], area_data['Amount'], label=area)
        ax2.yaxis.set_major_formatter(FuncFormatter(format_currency))
        ax2.legend()
        ax2.set_title("Monthly Trend")
        st.pyplot(fig2)

        st.subheader("📈 Month-over-Month Growth")
        growth = df.groupby(['Month', 'Business Area'])['Amount'].sum().unstack().pct_change().fillna(0) * 100
        growth_style = growth.style.format("{:.2f}%").background_gradient(cmap='RdYlGn', axis=0)
        st.dataframe(growth_style)

        st.subheader("📅 Weekday Performance")
        weekday_perf = df.groupby('Weekday')['Amount'].mean().reindex(
            ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        fig3, ax3 = plt.subplots()
        ax3.bar(weekday_perf.index, weekday_perf.values, color='orange')
        ax3.yaxis.set_major_formatter(FuncFormatter(format_currency))
        ax3.set_title("Average Amount by Day of Week")
        plt.xticks(rotation=45)
        st.pyplot(fig3)

        st.subheader("🏆 Top & Bottom Business Areas")
        top = agg.loc[agg['Amount'].idxmax()]
        bottom = agg.loc[agg['Amount'].idxmin()]
        top_bottom_df = pd.DataFrame([
            {'Label': 'Top Performer', 'Business Area': top['Business Area'], 'Amount': top['Amount']},
            {'Label': 'Lowest Performer', 'Business Area': bottom['Business Area'], 'Amount': bottom['Amount']},
        ])
        st.table(top_bottom_df)

        st.subheader("📊 Performance Scores")
        area_perf = df.groupby('Business Area').agg({
            'Amount': ['mean', 'std', 'count']
        })
        area_perf.columns = ['Mean', 'StdDev', 'Count']
        area_perf['Score'] = ((area_perf['Mean'] / area_perf['Mean'].max()) * 0.6 +
                              (1 - area_perf['StdDev'] / area_perf['StdDev'].max()) * 0.3 +
                              (area_perf['Count'] / area_perf['Count'].max()) * 0.1) * 10
        area_perf = area_perf.round(2)
        st.dataframe(area_perf[['Mean', 'StdDev', 'Score']])

        st.subheader("📝 Recommended Actions")
        for area, row in area_perf.iterrows():
            score = row['Score']
            if score < 5:
                st.warning(f"{area}: Performance review recommended.")
            elif score > 8:
                st.success(f"{area}: Strong – consider promotion.")
            else:
                st.info(f"{area}: Stable.")

        st.subheader("📄 Generate PDF")
        if st.button("Download PDF Report"):
            pdf_file = generate_pdf_v2(df, monthly, top_bottom_df, area_perf)
            if pdf_file:
                st.download_button("📅 Download Report", pdf_file, file_name="business_area_report.pdf", mime="application/pdf")
