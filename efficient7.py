import streamlit as st
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import numpy as np
import riskfolio as rp
from riskfolio import RiskfolioPortfolio


st.title("Racial Harm Portfolio Analyzer")

# Initialize session state for storing the DataFrame
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame(columns=[
        'Stock', 'Units', 'Purchase Date', 'Purchase Price', 'Current Price',
        'Initial Investment', 'Current Value', 'Gain/Loss', 'Gain/Loss %', 
        'Portfolio Allocation', 'GICS Sector', 'Normalized Harm Score'
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
    conn = sqlite3.connect('/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db')  # Update with your database path
    query = "SELECT Normalized_Score_2 FROM stockracialharm2 WHERE sector = ?"
    score = pd.read_sql_query(query, conn, params=(sector,))
    conn.close()
    
    if not score.empty:
        return score.iloc[0]['Normalized_Score_2']
    else:
        return None

# Function to optimize portfolio allocation using riskfolio-lib
def optimize_portfolio_allocation(df, max_harm_score):
    # Calculate returns and harm scores
    returns = df['Gain/Loss %'].str.replace('%', '').astype(float) / 100
    harm_scores = df['Normalized Harm Score'].astype(float)

    # Create a portfolio object
    port = rp.Portfolio(returns=returns.values)

    # Optimize using Mean-Variance Optimization (MVO)
    optimized_weights = port.optimization(model='Classic', objective='max_sharpe')

    # Apply harm score constraint manually
    while True:
        weighted_harm_score = np.dot(harm_scores, optimized_weights)
        if weighted_harm_score <= max_harm_score:
            break
        # If constraint is violated, reduce weights proportionally
        optimized_weights *= (max_harm_score / weighted_harm_score)

    # Update portfolio allocation based on optimized weights
    df['Portfolio Allocation'] = optimized_weights * 100  # Convert to percentage
    return df

# Move input fields to sidebar
with st.sidebar:
    st.header("Add Stock to Portfolio")
    with st.form("stock_form"):
        ticker = st.text_input("Enter stock ticker (e.g., AAPL, GOOGL)")
        units = st.number_input("Enter number of units", min_value=1, step=1)
        transaction_date = st.date_input("Select transaction date")
        submit_button = st.form_submit_button(label="Add to Portfolio")

# Add stock to portfolio logic here...
if submit_button:
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)
        hist = stock.history(start=transaction_date)
        
        if hist.empty:
            st.error("No data available for the selected date. Please choose a valid trading day.")
        else:
            # Get purchase price and current price
            purchase_price = hist.iloc[0]['Close']
            current_price = stock.info['currentPrice']
            
            # Calculate gain/loss and other metrics
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
                'Portfolio Allocation': ["0.00%"],  # Placeholder, will be updated later
                'GICS Sector': [gics_sector],
                'Normalized Harm Score': [normalized_score]  # Add normalized score here
            })
            
            # Append the new row to the existing DataFrame
            st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, new_row], ignore_index=True)
            
            # Update portfolio allocation
            st.session_state.portfolio_df = update_portfolio_allocation(st.session_state.portfolio_df)
            
            st.success(f"Added {ticker} to your portfolio with sector '{gics_sector}' and normalized score '{normalized_score}'.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Optimize portfolio if stocks are present and button is clicked
if not st.session_state.portfolio_df.empty and st.button("Optimize Portfolio"):
    max_harm_score = st.sidebar.number_input("Maximum Average Harm Score", min_value=0.0, step=0.01)
    
    mean_harm_score = st.session_state.portfolio_df['Normalized Harm Score'].astype(float).mean()
    
    if mean_harm_score <= max_harm_score:
        st.session_state.portfolio_df = optimize_portfolio_allocation(st.session_state.portfolio_df, max_harm_score)
        st.success("Portfolio optimized based on the maximum average harm score.")
        
        # Display the new DataFrame with optimized allocations above the plots
        st.subheader("Optimized Portfolio Allocations")
        st.dataframe(st.session_state.portfolio_df[['Stock', 'Portfolio Allocation']])
        
    else:
        st.warning(f"Mean harm score {mean_harm_score:.2f} exceeds the maximum allowed score of {max_harm_score:.2f}.")



# Display the portfolio table and other visualizations...
if not st.session_state.portfolio_df.empty:
    st.subheader("Your Portfolio")
    st.dataframe(st.session_state.portfolio_df)

    # Create two columns for side-by-side layout for visualizations
    col1, col2 = st.columns(2)

    # Create a doughnut chart for normalized harm scores in the first column
    harm_scores_df = st.session_state.portfolio_df[['Stock', 'Normalized Harm Score']]
    
    if not harm_scores_df['Normalized Harm Score'].isnull().all():
        harm_scores_df['Normalized Harm Score'] = harm_scores_df['Normalized Harm Score'].astype(float)
        
        fig1 = px.pie(harm_scores_df, 
                     names='Stock', 
                     values='Normalized Harm Score',
                     hole=0.4,
                     title="Stock Portfolio Harm Profile",
                     labels={'Normalized Harm Score': 'Harm Score'})
        
        with col1:
            st.plotly_chart(fig1)

    # Calculate normalized harm score * number of units and percentage of total harm scores times units.
    
    total_harm_score_units = (st.session_state.portfolio_df['Normalized Harm Score'].astype(float) *
                               st.session_state.portfolio_df['Units']).sum()
    
    st.session_state.portfolio_df['Harm Score Contribution (%)'] = (
       (st.session_state.portfolio_df['Normalized Harm Score'].astype(float) *
         st.session_state.portfolio_df['Units']) / total_harm_score_units * 100).fillna(0)

    contribution_data = st.session_state.portfolio_df[['Stock', 'Harm Score Contribution (%)']]
    
    if not contribution_data['Harm Score Contribution (%)'].isnull().all():
       contribution_data['Harm Score Contribution (%)'] = contribution_data['Harm Score Contribution (%)'].astype(float)
    
       fig2 = px.pie(contribution_data, 
                      names='Stock', 
                      values='Harm Score Contribution (%)',
                      title="Portfolio Harm Contribution by Stock",
                      labels={'Harm Score Contribution (%)': 'Contribution (%)'},
                      hole=0.4)  

       with col2:
           st.plotly_chart(fig2)

# Option to remove stocks from portfolio in sidebar
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


