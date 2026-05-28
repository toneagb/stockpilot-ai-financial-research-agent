import os
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="StockPilot", layout="wide")

st.title("StockPilot")
st.subheader("AI Financial Market Research Agent")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Missing GEMINI_API_KEY. Add it to a .env file or Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

ticker = st.text_input("Enter a stock ticker:", value="AAPL").upper().strip()

if st.button("Generate Report"):
    if not ticker:
        st.warning("Please enter a ticker.")
        st.stop()

    with st.spinner("Fetching stock data..."):
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")

    if hist.empty:
        st.error("No stock data found. Please check the ticker.")
        st.stop()

    info = stock.info

    company_name = info.get("longName", ticker)
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    market_cap = info.get("marketCap", "N/A")

    current_price = hist["Close"].iloc[-1]
    start_price = hist["Close"].iloc[0]
    percent_change = ((current_price - start_price) / start_price) * 100

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Company", company_name)
    col2.metric("Current Price", f"${current_price:.2f}")
    col3.metric("6-Month Change", f"{percent_change:.2f}%")
    col4.metric("Sector", sector)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["Close"],
            mode="lines",
            name=f"{ticker} Close Price"
        )
    )

    fig.update_layout(
        title=f"{company_name} ({ticker}) - 6 Month Price History",
        xaxis_title="Date",
        yaxis_title="Close Price",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    try:
        news_items = stock.news[:5]
        news_headlines = [
            item.get("title", "No title") for item in news_items
        ]
    except Exception:
        news_headlines = []

    news_text = "\n".join(
        [f"- {headline}" for headline in news_headlines]
    ) if news_headlines else "No recent headlines available."

    prompt = f"""
You are StockPilot, an AI financial market research agent.

Generate a structured financial research report for the following company.

Company: {company_name}
Ticker: {ticker}
Sector: {sector}
Industry: {industry}
Market Cap: {market_cap}
Current Price: {current_price:.2f}
Six-Month Price Change: {percent_change:.2f}%

Recent News Headlines:
{news_text}

Your report should include:
1. Company Overview
2. Recent Price Trend Summary
3. News Highlights
4. AI Market Commentary
5. Key Risks or Limitations
6. Disclaimer that this is not financial advice

Write clearly for a beginner finance student.
"""

    with st.spinner("Generating AI report..."):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

    st.markdown("## AI Financial Research Report")
    st.markdown(response.text)