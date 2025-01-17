import streamlit as st
import pandas as pd
import sqlite3
from flashtext import KeywordProcessor
from playwright.sync_api import sync_playwright
import base64
import hmac

st.set_page_config(layout="wide")

@st.cache_resource
def get_connection():
    return sqlite3.connect('nycprocurement.db', check_same_thread=False)

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

def capture_screenshot_and_convert_to_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8501")
        pdf_bytes = page.pdf()
        browser.close()
    return pdf_bytes

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        print(st.secrets)
        if st.session_state["username"] in st.secrets["passwords"] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


if not check_password():
    st.stop()

def main():
    # Initialize session state variables if they don't exist
    if 'search_clicked' not in st.session_state:
        st.session_state.search_clicked = False
    if 'results' not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = pd.DataFrame()
    if 'previous_selection' not in st.session_state:
        st.session_state.previous_selection = set()

    # Initialize combined_df only after keyword matching is done
    combined_df = None  

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
            # Display search results
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

            # Display selected records
            st.write("User Selected Records:")
            st.dataframe(st.session_state.selected_rows, hide_index=True)

            # Initialize combined_df here after user selections are made 
            combined_df = pd.DataFrame()  # Initialize combined_df only after selections

            # Display the full table of awards
            query = "SELECT * FROM nycproawards4"
            df_awards = pd.read_sql_query(query, conn)
            
            # Combine awards data into the combined DataFrame
            combined_df = pd.concat([combined_df, df_awards], ignore_index=True)
            
            # Display awards data
            st.dataframe(df_awards, use_container_width=True)

            # FlashText keyword matching (if needed)
            if not (st.session_state.selected_rows.empty or keyword == ""):
                keyword_processor = KeywordProcessor()
                keyword_processor.add_keyword(keyword)

                matched_rows = []
                for _, row in df_awards.iterrows():
                    if keyword_processor.extract_keywords(row['Title']):
                        matched_rows.append(row)

                if matched_rows:
                    matched_df = pd.DataFrame(matched_rows)
                    combined_df = pd.concat([combined_df, matched_df], ignore_index=True)  # Add matches to combined DataFrame

                    # Button to download combined CSV file
                    csv_file_name = 'combined_results.csv'
                    if not combined_df.empty:
                        csv_bytes = combined_df.to_csv(index=False).encode('utf-8')
                        b64_csv = base64.b64encode(csv_bytes).decode('utf-8')
                        href_csv = f'<a href="data:file/csv;base64,{b64_csv}" download="{csv_file_name}">Download Combined CSV</a>'
                        st.markdown(href_csv, unsafe_allow_html=True)

if __name__ == "__main__":
   main()
