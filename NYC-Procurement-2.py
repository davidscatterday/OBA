import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Connect to the SQLite database
@st.cache_resource
def get_connection():
    return sqlite3.connect('/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db', check_same_thread=False)

conn = get_connection()

# Function to search data based on all filters
@st.cache_data
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
@st.cache_data
def get_unique_values(column):
    query = f"SELECT DISTINCT \"{column}\" FROM newtable WHERE \"{column}\" IS NOT NULL AND \"{column}\" != ''"
    return [row[0] for row in conn.execute(query).fetchall()]

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

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
        st.session_state.search_clicked = True
        # Check if any additional filters are set
        additional_filters_set = any([agency, procurement_method, fiscal_quarter, job_titles, headcount])

        if keyword or additional_filters_set:
            st.session_state.results = search_data(
                keyword, agency, procurement_method,
                fiscal_quarter, job_titles, headcount
            )
        else:
            st.session_state.results = pd.DataFrame()

        # Ensure the session state variables are initialized
        if 'results' not in st.session_state:
            st.session_state.results = pd.DataFrame()  # Initialize with your actual data
        if 'selected_rows' not in st.session_state:
            st.session_state.selected_rows = pd.DataFrame()
        if 'previous_selection' not in st.session_state:
            st.session_state.previous_selection = set()


        # Display results
        if st.session_state.search_clicked:
            if not st.session_state.results.empty:
                st.write(f"Found {len(st.session_state.results)} results:")

                # Add a checkbox column to the DataFrame
                results_with_checkbox = st.session_state.results.copy()
                results_with_checkbox['Select'] = False

                # Display the DataFrame with checkboxes
                edited_df = st.data_editor(
                    results_with_checkbox,
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", default=False)
                    },
                    disabled=results_with_checkbox.columns.drop('Select').tolist(),
                    key="editable_dataframe"
                )

                # Check for changes in the DataFrame
                if not edited_df.equals(results_with_checkbox):
                    # Get the currently selected rows
                    current_selection = set(edited_df[edited_df['Select']].index)
                    
                    # Find newly selected rows
                    new_selections = current_selection - st.session_state.previous_selection
                    
                    # Add only the newly selected rows to the selected_rows DataFrame
                    new_rows = edited_df.loc[list(new_selections)].drop(columns=['Select'])
                    st.session_state.selected_rows = pd.concat([st.session_state.selected_rows, new_rows], ignore_index=True)
                    
                    # Update the previous selection
                    st.session_state.previous_selection = current_selection

                # Display the selected rows
                st.write("Selected Rows:")
                st.dataframe(st.session_state.selected_rows, hide_index=True)
                
                # Download button for search results
                csv = convert_df_to_csv(st.session_state.results)
                st.download_button(
                    label="Download search results as CSV",
                    data=csv,
                    file_name=f"nyc_procurement_search_results_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.write("No results found.")
    else:
        st.write("Please enter a keyword or select at least one filter and click 'Search'.")

if __name__ == "__main__":
    main()