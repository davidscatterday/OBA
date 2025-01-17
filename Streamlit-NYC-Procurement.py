import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect('/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db')

# Function to search data based on all filters
def search_data(keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount):
    query = """
    SELECT * FROM newtable
    WHERE "Services Descrption" LIKE ?
    """
    params = [f'%{keyword}%']

    if agency:
        query += ' AND "Agency" = ?'
        params.append(agency)
    if procurement_method:
        query += ' AND "Procurement Method" = ?'
        params.append(procurement_method)
    if fiscal_quarter:
        query += ' AND "Fiscal Quarter" = ?'
        params.append(fiscal_quarter)
    if job_titles:
        query += ' AND "Job Titles" = ?'
        params.append(job_titles)
    if headcount:
        query += ' AND "Head-count" = ?'
        params.append(headcount)

    df = pd.read_sql_query(query, conn, params=params)
    return df

# Function to get unique values for dropdown filters
def get_unique_values(column):
    query = f"SELECT DISTINCT \"{column}\" FROM newtable WHERE \"{column}\" IS NOT NULL AND \"{column}\" != ''"
    return [row[0] for row in conn.execute(query).fetchall()]



# Streamlit app and main content
def main():
    st.title("NYC Procurement Intelligence")
    st.markdown("<h5 style='text-align: left; color: #888888;'>Pinpoint Commercial Opportunities with the City of New York</h5>", unsafe_allow_html=True)

    st.write("")  # This adds an empty line
    st.write("")  # This adds an empty line
    st.write("")  # This adds an empty line
    
    # Sidebar for filters
    st.sidebar.header("Search Filters")

    # Keyword search
    keyword = st.sidebar.text_input("Keyword Search (Services Description)")

    # Dropdown filters
    agency = st.sidebar.selectbox("Agency", [""] + get_unique_values("Agency"))
    procurement_method = st.sidebar.selectbox("Procurement Method", [""] + get_unique_values("Procurement Method"))
    fiscal_quarter = st.sidebar.selectbox("Fiscal Quarter", [""] + get_unique_values("Fiscal Quarter"))
    job_titles = st.sidebar.selectbox("Job Titles", [""] + get_unique_values("Job Titles"))
    headcount = st.sidebar.selectbox("Head-count", [""] + [str(x) for x in get_unique_values("Head-count")])

     # Search button
    if st.sidebar.button("Search"):
        # Check if any additional filters are set
        additional_filters_set = any([agency, procurement_method, fiscal_quarter, job_titles, headcount])

        if keyword or additional_filters_set:
            results = search_data(
                keyword, agency, procurement_method,
                fiscal_quarter, job_titles, headcount
            )
            
            if not results.empty:
                st.write(f"Found {len(results)} results:")
                st.dataframe(results)
            else:
                st.write("No results found.")
        else:
            st.write("Please enter a keyword or select at least one filter.")

if __name__ == "__main__":
    main()