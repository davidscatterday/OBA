import streamlit as st
st.set_page_config(layout="wide")  # Set the page layout to wide
import pandas as pd
import sqlite3
import recordlinkage
import flashtext

# Function to get database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect('/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db', check_same_thread=False)

# Use the cached connection
conn = get_connection()

# Function to get unique values from a column
@st.cache_data
def get_unique_values(column):
    query = f"SELECT DISTINCT `{column}` FROM newtable ORDER BY `{column}`"
    return pd.read_sql_query(query, conn)[column].tolist()

# Function to search data
@st.cache_data
def search_data(keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount):
    query = """
    SELECT * FROM newtable
    WHERE "Services Descrption" LIKE ?
    """
    params = [f'%{keyword}%']

    if keyword:
        query += " AND `Services Descrption` LIKE ?"
        params.append(f"%{keyword}%")
    if agency:
        query += " AND Agency = ?"
        params.append(agency)
    if procurement_method:
        query += " AND `Procurement Method` = ?"
        params.append(procurement_method)
    if fiscal_quarter:
        query += " AND `Fiscal Quarter` = ?"
        params.append(fiscal_quarter)
    if job_titles:
        query += " AND `Job Titles` = ?"
        params.append(job_titles)
    if headcount:
        query += " AND `Head-count` = ?"
        params.append(headcount)

    return pd.read_sql_query(query, conn, params=params)

def main():
    # Initialize session state variables if they do not exist
    if 'search_clicked' not in st.session_state:
        st.session_state.search_clicked = False
    if 'results' not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = pd.DataFrame()
    if 'previous_selection' not in st.session_state:
        st.session_state.previous_selection = set()

    st.title("NYC Procurement Intelligence")
    st.markdown("<h5 style='text-align: left; color: #888888;'>Pinpoint Commercial Opportunities with the City of New York</h5>", unsafe_allow_html=True)

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
        additional_filters_set = any([agency, procurement_method, fiscal_quarter, job_titles, headcount])

        if keyword or additional_filters_set:
            st.session_state.results = search_data(
                keyword, agency, procurement_method,
                fiscal_quarter, job_titles, headcount)
        else:
            st.session_state.results = pd.DataFrame()

    # Display results
    if st.session_state.search_clicked:
        if not st.session_state.results.empty:
            st.write(f"Found {len(st.session_state.results)} results:")

            # Create a new DataFrame with 'Select' as the first column
            select_column = pd.DataFrame({'Select': False}, index=st.session_state.results.index)
            results_with_checkbox = pd.concat([select_column, st.session_state.results], axis=1)

            # Display the DataFrame with checkboxes
            edited_df = st.data_editor(
                results_with_checkbox,
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", default=False)
                },
                disabled=results_with_checkbox.columns.drop('Select').tolist(),
                key="editable_dataframe",
                use_container_width=True
            )

            # Check for changes in the DataFrame
            current_selection = set(edited_df[edited_df['Select']].index)
            new_selections = current_selection - st.session_state.previous_selection
            deselections = st.session_state.previous_selection - current_selection

            # Add newly selected rows
            new_rows = edited_df.loc[list(new_selections)].drop(columns=['Select'])
            st.session_state.selected_rows = pd.concat([st.session_state.selected_rows, new_rows], ignore_index=True)

            # Remove deselected rows
            st.session_state.selected_rows = st.session_state.selected_rows[~st.session_state.selected_rows.index.isin(deselections)]

            # Update the previous selection
            st.session_state.previous_selection = current_selection

            # Display the selected rows
            st.write("Selected Records:")
            st.dataframe(st.session_state.selected_rows, hide_index=True)

            # Perform record linkage
            if not st.session_state.selected_rows.empty:
                st.write("Record Linkage Results:")
                
                # Query all rows from the nycproawards4 table
                query = "SELECT * FROM nycproawards4"
                df_awards = pd.read_sql_query(query, conn)

                # Perform record linkage
                indexer = recordlinkage.Index()

                # Set up the blocking method to compare 'Services Description' from selected_rows
                # with 'Title' from df_awards
                indexer.block(left_on='Services Descrption', right_on='Title')

                # Perform the indexing
                candidate_links = indexer.index(st.session_state.selected_rows, df_awards)
                
                compare = recordlinkage.Compare()
                compare.string('Services Descrption', 'Title', method='jarowinkler', threshold=0.45, label='Title_Match')
                
                features = compare.compute(candidate_links, st.session_state.selected_rows, df_awards)
                
                # Get matches above a certain threshold
                matches = features[features.sum(axis=1) > 0.85]
                
                # Prepare results for display
                matched_df = pd.DataFrame(index=matches.index)
                matched_df['Services Description'] = matches.index.get_level_values(0).map(st.session_state.selected_rows['Services Descrption'])
                matched_df['Best Match (Title)'] = matches.index.get_level_values(1).map(df_awards['Title'])
                matched_df['Match Score'] = matches['Title_Match']
                
                # Display the record linkage results
                st.dataframe(matched_df, hide_index=True)
                
                # Optional: Display detailed matches
                st.write("Detailed Matches:")
                for index, row in matched_df.iterrows():
                    st.write(f"Services Description (newtable): {row['Services Description']}")
                    st.write(f"Best Match Title (nycproawards4): {row['Best Match (Title)']}")
                    st.write(f"Match Score: {row['Match Score']}")
                    st.write("---")
            
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a keyword or select at least one filter and click 'Search'.")

    # Display the full table
    st.header("FY25 NYC Government Procurement Awards")
    query = "SELECT * FROM nycproawards4"
    df = pd.read_sql_query(query, conn)
    st.dataframe(df)

if __name__ == "__main__":
    main()

# Note: We don't close the connection here because it's a cached resource
# The connection will be closed when the Streamlit app is shut down