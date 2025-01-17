import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import okama as ok
import random
import numpy as np




# Add custom CSS to make elements span full width

st.markdown("""

<style>
/* Ensure full width for horizontal blocks and columns */
.stApp [data-testid="stHorizontalBlock"] {
    width: 100%;
    max-width: 100%;
    padding-left; -100;
}

.stApp [data-testid="column"] {
    width: 100%;
    max-width: 100%;
}

/* Targeting the specific DataFrame by its data-testid */
.stApp [data-testid="stDataFrame"] {
    width: 100% !important; /* Force full width */
}

/* Ensure that all table headers and cells span full width */
table {
    width: 100% !important; /* Force table to take full width */
}

th, td {
    white-space: nowrap; /* Prevent text wrapping */
    text-align: left; /* Align text to the left for better readability */
}

/* New CSS to remove space between header and charts */
.stMarkdown h2 {
    margin-bottom: 0;
    padding-bottom: 0;
}

.stPlotlyChart {
    margin-top: 0;
    padding-top: -110;
}

/* Optional styling for better visibility */
th {
    background-color: #f2f2f2; /* Light gray background for headers */
}
</style>
""", unsafe_allow_html=True)

st.title("Stock Portfolio Analyzer")

# Initialize session state for storing the DataFrame
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame(columns=[
        'Stock', 'Units', 'Purchase Date', 'Purchase Price', 'Current Price',
        'Initial Investment', 'Current Value', 'Gain/Loss', 'Gain/Loss %', 'Portfolio Allocation', 'GICS Industry'
    ])

# Function to update portfolio allocation
def update_portfolio_allocation(df):
    if not df.empty:
        total_value = df['Current Value'].str.replace('$', '').astype(float).sum()
        df['Portfolio Allocation'] = df['Current Value'].str.replace('$', '').astype(float) / total_value * 100
        df['Portfolio Allocation'] = df['Portfolio Allocation'].apply(lambda x: f"{x:.2f}%")
    return df

# Function to get GICS Industry
def get_gics_industry(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info.get('industry', 'N/A')
    except:
        return 'N/A'

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
            
            # Get historical data
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
            
            # Get GICS Industry
            gics_industry = get_gics_industry(ticker)
            
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
                'GICS Industry': [gics_industry]
            })
            
            # Append the new row to the existing DataFrame
            st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, new_row], ignore_index=True)
            
            # Update portfolio allocation
            st.session_state.portfolio_df = update_portfolio_allocation(st.session_state.portfolio_df)
            
            st.success(f"Added {ticker} to your portfolio.")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display the portfolio table
if not st.session_state.portfolio_df.empty:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Your Portfolio")
    st.dataframe(st.session_state.portfolio_df)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add option to remove stocks
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


# Main body
 # Portfolio Summary
if not st.session_state.portfolio_df.empty:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>Portfolio Summary</h2>', unsafe_allow_html=True)
    portfolio_value = st.session_state.portfolio_df['Current Value'].str.replace('$', '').astype(float).sum()
    st.metric("Total Portfolio Value", f"${portfolio_value:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)


    # Create two sunburst charts
    st.markdown("## Portfolio Analysis")
    fig = make_subplots(
    rows=2, cols=2, 
    specs=[[{'type':'domain'}, {'type':'domain'}], [{'type':'domain', 'colspan': 2}, None]],
    subplot_titles=("Portfolio Allocation by Industry and Stock", "Portfolio Returns Driver", "GICS Industry Groups and Sub-Industries")
)
    
    
    # First sunburst chart (Portfolio Allocation)
    chart_data = st.session_state.portfolio_df.copy()
    chart_data['Current Value'] = chart_data['Current Value'].str.replace('$', '').astype(float)
    
    sunburst1 = px.sunburst(
        chart_data,
        path=['GICS Industry', 'Stock'],
        values='Current Value',
        title='Portfolio Allocation by Industry and Stock',
    )
    
    # Second sunburst chart (Portfolio Returns Driver)
    returns_data = chart_data[chart_data['Gain/Loss %'].str.rstrip('%').astype(float) > 0].copy()
    returns_data['Positive Return'] = returns_data['Gain/Loss %'].str.rstrip('%').astype(float)
    
    sunburst2 = px.sunburst(
        returns_data,
        path=['GICS Industry', 'Stock'],
        values='Positive Return',
        title='Portfolio Returns Driver',
    )
    
    # Add traces to subplots (sunburst charts)
    fig.add_trace(sunburst1.data[0], row=1, col=1)
    fig.add_trace(sunburst2.data[0], row=1, col=2)
    
    # Generate GICS treemap data
    industry_groups = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary", "Consumer Staples",
        "Health Care", "Financials", "Information Technology", "Communication Services",
        "Utilities", "Real Estate"
    ]
    treemap_data = []
    for group in industry_groups:
        num_sub_industries = random.randint(3, 8)
        for i in range(num_sub_industries):
            sub_industry = f"{group} Sub-Industry {i+1}"
            value = random.randint(100, 1000)
            treemap_data.append({
                "Industry Group": group,
                "Sub-Industry": sub_industry,
                "Value": value
            })
    treemap_df = pd.DataFrame(treemap_data)

    # Create GICS treemap
    treemap = px.treemap(
        treemap_df,
        path=['Industry Group', 'Sub-Industry'],
        values='Value',
        color='Industry Group',
        color_continuous_scale='RdBu'
    )
    
    # Add treemap to the subplot
    for trace in treemap.data:
        fig.add_trace(trace, row=2, col=1)

    # Update layout
    fig.update_layout(
        width=1000,
        height=1200,
    )
    
    # Update subplot titles
    fig.update_annotations(font_size=12)
    
    # Display the charts
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Add stocks to your portfolio to see analysis.")