import streamlit as st
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
from plotly.subplots import make_subplots
import random

st.title("Stock Portfolio Analyzer")

# Initialize session state for storing the DataFrame
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame(columns=[
        'Stock', 'Units', 'Purchase Date', 'Purchase Price', 'Current Price',
        'Initial Investment', 'Current Value', 'Gain/Loss', 'Gain/Loss %', 
        'Portfolio Allocation', 'GICS Sector'
    ])

# Function to update portfolio allocation
def update_portfolio_allocation(df):
    if not df.empty:
        total_value = df['Current Value'].str.replace('$', '').astype(float).sum()
        df['Portfolio Allocation'] = df['Current Value'].str.replace('$', '').astype(float) / total_value * 100
        df['Portfolio Allocation'] = df['Portfolio Allocation'].apply(lambda x: f"{x:.2f}%")
    return df

# Function to get GICS Sector
def get_gics_sector(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info.get('sector', 'N/A')  # Retrieve sector instead of industry
    except:
        return 'N/A'

# Function to get normalized score from SQLite database based on sector
def get_normalized_score(sector):
    conn = sqlite3.connect('/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db')
    query = "SELECT Normalized_Score_2 FROM stockracialharm2 WHERE sector = ?"
    score = pd.read_sql_query(query, conn, params=(sector,))
    conn.close()
    
    if not score.empty:
        return score.iloc[0]['Normalized_Score_2']
    else:
        return None

# Move input fields to sidebar
with st.sidebar:
    st.header("Add Stock to Portfolio")
    with st.form("stock_form"):
        ticker = st.text_input("Enter stock ticker (e.g., AAPL, GOOGL)")
        units = st.number_input("Enter number of units", min_value=1, step=1)
        transaction_date = st.date_input("Select transaction date")
        submit_button = st.form_submit_button(label="Add to Portfolio")

    if submit_button:
        try:
            # Fetch stock data
            stock = yf.Ticker(ticker)
            hist = stock.history(start=transaction_date)
            
            if hist.empty:
                st.error("No data available for the selected date. Please choose a valid trading day.")
            else:
                # Get purchase price
                purchase_price = hist.iloc[0]['Close']
                # Get current price
                current_price = stock.info['currentPrice']
                
                # Calculate gain/loss
                initial_investment = purchase_price * units
                current_value = current_price * units
                gain_loss = current_value - initial_investment
                gain_loss_percentage = (gain_loss / initial_investment) * 100
                
                # Get GICS Sector and normalized score
                gics_sector = get_gics_sector(ticker)
                normalized_score = get_normalized_score(gics_sector)

                # Create a new row for the DataFrame
                new_row = pd.DataFrame({
                    'Stock': [ticker],
                    'Units': [units],
                    'Purchase Date': [transaction_date],
                    'Purchase Price': [f"${purchase_price:.2f}"],
                    'Current Price': [f"${current_price:.2f}"],
                    'Initial Investment': [f"${initial_investment:.2f}"],
                    'Current Value': [f"${current_value:.2f}"],
                    'Gain/Loss': [f"${gain_loss:.2f}"],
                    'Gain/Loss %': [f"{gain_loss_percentage:.2f}%"],
                    'Portfolio Allocation': ["0.00%"],  # Placeholder, will be updated
                    'GICS Sector': [gics_sector]
                })
                
                # Append the new row to the existing DataFrame
                st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, new_row], ignore_index=True)
                
                # Update portfolio allocation
                st.session_state.portfolio_df = update_portfolio_allocation(st.session_state.portfolio_df)
                
                st.success(f"Added {ticker} to your portfolio with sector '{gics_sector}' and normalized score '{normalized_score}'.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display the portfolio table
if not st.session_state.portfolio_df.empty:
    st.subheader("Your Portfolio")
    st.dataframe(st.session_state.portfolio_df)

# Add option to remove stocks from portfolio
with st.sidebar:
    st.header("Remove Stocks from Portfolio")
    stocks_to_remove = st.multiselect("Select stocks to remove", 
                                      options=st.session_state.portfolio_df['Stock'].unique())

    if st.button("Remove Selected Stocks"):
        st.session_state.portfolio_df = st.session_state.portfolio_df[
            ~st.session_state.portfolio_df['Stock'].isin(stocks_to_remove)]
        
        # Update portfolio allocation after removal
        st.session_state.portfolio_df = update_portfolio_allocation(st.session_state.portfolio_df)
        st.success("Selected stocks removed from portfolio.")

# Portfolio Summary and Analysis Section
if not st.session_state.portfolio_df.empty:
    portfolio_value = st.session_state.portfolio_df['Current Value'].str.replace('$', '').astype(float).sum()
    
    # Display total portfolio value
    st.metric("Total Portfolio Value", f"${portfolio_value:.2f}")
else:
    st.info("Add stocks to your portfolio to see analysis.")
