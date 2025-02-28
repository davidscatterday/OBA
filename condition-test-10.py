import streamlit as st
import pandas as pd
import sqlite3
from flashtext import KeywordProcessor
from playwright.sync_api import sync_playwright
import base64

st.set_page_config(layout="wide")

@st.cache_resource
def get_connection():
    return sqlite3.connect('/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db', check_same_thread=False)

conn = get_connection()

@st.cache_data
def get_unique_values(column):
    query = f"SELECT DISTINCT `{column}` FROM newtable ORDER BY `{column}`"
    return pd.read_sql_query(query, conn)[column].tolist()

@st.cache_data
def search_data(keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount):
    query = "SELECT * FROM newtable WHERE 1=1"
    params = []
    
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

    st.sidebar.header("Search Filters")
    keyword = st.sidebar.text_input("Keyword Search (Services Description)")
    agency = st.sidebar.selectbox("Agency", [""] + get_unique_values("Agency"))
    procurement_method = st.sidebar.selectbox("Procurement Method", [""] + get_unique_values("Procurement Method"))
    fiscal_quarter = st.sidebar.selectbox("Fiscal Quarter", [""] + get_unique_values("Fiscal Quarter"))
    job_titles = st.sidebar.selectbox("Job Titles", [""] + get_unique_values("Job Titles"))
    headcount = st.sidebar.selectbox("Head-count", [""] + [str(x) for x in get_unique_values("Head-count")])

    if st.sidebar.button("Search"):
        st.session_state.search_clicked = True
        additional_filters_set = any([agency, procurement_method, fiscal_quarter, job_titles, headcount])

        if keyword or additional_filters_set:
            st.session_state.results = search_data(keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount)
        else:
            st.session_state.results = pd.DataFrame()

    if st.session_state.search_clicked:
        if not st.session_state.results.empty:
            st.write(f"Found {len(st.session_state.results)} results:")

            select_column = pd.DataFrame({'Select': False}, index=st.session_state.results.index)
            results_with_checkbox = pd.concat([select_column, st.session_state.results], axis=1)

            edited_df = st.data_editor(
                results_with_checkbox,
                hide_index=True,
                column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
                disabled=results_with_checkbox.columns.drop('Select').tolist(),
                key="editable_dataframe",
                use_container_width=True
            )

            current_selection = set(edited_df[edited_df['Select']].index)
            new_selections = current_selection - st.session_state.previous_selection
            deselections = st.session_state.previous_selection - current_selection

            new_rows = edited_df.loc[list(new_selections)].drop(columns=['Select'])
            st.session_state.selected_rows = pd.concat([st.session_state.selected_rows, new_rows], ignore_index=True)
            st.session_state.selected_rows = st.session_state.selected_rows[~st.session_state.selected_rows.index.isin(deselections)]
            st.session_state.previous_selection = current_selection

            st.write("User Selected Records:")
            st.dataframe(st.session_state.selected_rows, hide_index=True)

    # Display the full table
    st.markdown("Fiscal Year 2025 NYC Government Procurement Awards")
    query = "SELECT * FROM nycproawards4"
    df_awards = pd.read_sql_query(query, conn)
    st.dataframe(df_awards, use_container_width=True)
   
    # FlashText keyword matching
    if not st.session_state.selected_rows.empty and keyword:
        st.markdown("Keyword Matches")
        keyword_processor = KeywordProcessor()
        keyword_processor.add_keyword(keyword)

        matched_rows = []
        for _, row in st.session_state.selected_rows.iterrows():
            if keyword_processor.extract_keywords(row['Services Descrption']):
                matched_rows.append(row)

        for _, row in df_awards.iterrows():
            if keyword_processor.extract_keywords(row['Title']):
                matched_rows.append(row)

        if matched_rows:
            st.dataframe(pd.DataFrame(matched_rows))
        else:
            st.write("No keyword matches found.")

if __name__ == "__main__":
    main()