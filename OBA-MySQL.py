import streamlit as st
import pandas as pd
import mysql.connector
import hmac
from flashtext import KeywordProcessor
import pytz
import threading
import schedule
import time
from datetime import datetime
from scrapper_mysql import scraper

target_tz = pytz.timezone('America/New_York')

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_scraper():
    print("schedule scrapper")
    scraper()

schedule.every().day.at("11:10").do(run_scraper)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()
st.set_page_config(layout="wide")

@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host='sql.freedb.tech',
        user='freedb_davidscatterday',
        password='KC55*RM*F8ujyfn',
        database='freedb_NYCtest'
    )

conn = get_connection()

@st.cache_data
def get_unique_values(column):
    cursor = conn.cursor()
    query = f"SELECT DISTINCT `{column}` FROM nycproawards4 ORDER BY `{column}`"
    cursor.execute(query)
    result = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return result

@st.cache_data
def search_data(keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount):
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM newtable WHERE 1=1"
    params = []
    
    if keyword:
        query += " AND `Services Descrption` LIKE %s"
        params.append(f"%{keyword}%")
    if agency:
        query += " AND Agency = %s"
        params.append(agency)
    if procurement_method:
        query += " AND `Procurement Method` = %s"
        params.append(procurement_method)
    if fiscal_quarter:
        query += " AND `Fiscal Quarter` = %s"
        params.append(fiscal_quarter)
    if job_titles:
        query += " AND `Job Titles` = %s"
        params.append(job_titles)
    if headcount:
        query += " AND `Head-count` = %s"
        params.append(headcount)
    
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(result)

def check_password():
    def login_form():
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

def reset_all_states():
    session_vars = [
        'search_clicked',
        'results',
        'selected_rows',
        'previous_selection',
        'editable_dataframe',
        'show_results',
        'show_awards',
        'show_matches'
    ]
    
    for var in session_vars:
        if var in st.session_state:
            del st.session_state[var]
    
    st.cache_data.clear()
    
    st.session_state.reset_trigger = True
    st.rerun()

def main():
    if 'reset_trigger' not in st.session_state:
        st.session_state.reset_trigger = False

    if 'search_clicked' not in st.session_state:
        st.session_state.search_clicked = False
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'show_awards' not in st.session_state:
        st.session_state.show_awards = False
    if 'show_matches' not in st.session_state:
        st.session_state.show_matches = False
    if 'results' not in st.session_state:
        st.session_state.results = pd.DataFrame()
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = pd.DataFrame()
    if 'previous_selection' not in st.session_state:
        st.session_state.previous_selection = set()

    st.title("NYC Procurement Intelligence")
    st.markdown(
        "<h5 style='text-align: left; color: #888888;'>Pinpoint Commercial Opportunities with the City of New York</h5>",
        unsafe_allow_html=True,
    )

    st.sidebar.header("Search Filters")

    default_value = "" if st.session_state.get('reset_trigger', False) else st.session_state.get('keyword', "")
    default_index = 0 if st.session_state.get('reset_trigger', False) else None
    
    keyword = st.sidebar.text_input(
        "Keyword Search (Services Description)",
        value=default_value,
        key="keyword"
    )
    
    agency = st.sidebar.selectbox(
        "Agency",
        [""] + get_unique_values("Agency"),
        index=default_index,
        key="agency"
    )
    
    procurement_method = st.sidebar.selectbox(
        "Procurement Method",
        [""] + get_unique_values("Procurement Method"),
        index=default_index,
        key="procurement_method"
    )
    
    fiscal_quarter = st.sidebar.selectbox(
        "Fiscal Quarter",
        [""] + get_unique_values("Fiscal Quarter"),
        index=default_index,
        key="fiscal_quarter"
    )
    
    job_titles = st.sidebar.selectbox(
        "Job Titles",
        [""] + get_unique_values("Job Titles"),
        index=default_index,
        key="job_titles"
    )
    
    headcount = st.sidebar.selectbox(
        "Head-count",
        [""] + [str(x) for x in get_unique_values("Head-count")],
        index=default_index,
        key="headcount"
    )

    if st.session_state.get('reset_trigger', False):
        st.session_state.reset_trigger = False

    filters_applied = any([keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount])

    if st.sidebar.button("Search"):
        if filters_applied:
            st.session_state.search_clicked = True
            st.session_state.show_results = True
            st.session_state.show_awards = True
            st.session_state.show_matches = True
            st.session_state.results = search_data(
                keyword, agency, procurement_method, fiscal_quarter, job_titles, headcount
            )
        else:
            st.warning("Please apply at least one filter before searching.")
            st.session_state.show_results = False
            st.session_state.show_awards = False
            st.session_state.show_matches = False

    if st.sidebar.button("Reset Search"):
        reset_all_states()
        st.rerun()

    if st.session_state.show_results and not st.session_state.results.empty:
        st.write(f"Found {len(st.session_state.results)} results:")
        select_column = pd.DataFrame({'Select': False}, index=st.session_state.results.index)
        results_with_checkbox = pd.concat([select_column, st.session_state.results], axis=1)

        edited_df = st.data_editor(
            results_with_checkbox,
            hide_index=True,
            column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
            disabled=results_with_checkbox.columns.drop('Select').tolist(),
            key="editable_dataframe",
            use_container_width=True,
        )

        current_selection = set(edited_df[edited_df['Select']].index)
        new_selections = current_selection - st.session_state.previous_selection
        deselections = st.session_state.previous_selection - current_selection

        if not st.session_state.selected_rows.empty:
            new_rows = edited_df.loc[list(new_selections)].drop(columns=['Select'])
            st.session_state.selected_rows = pd.concat(
                [st.session_state.selected_rows, new_rows], ignore_index=True
            )
            st.session_state.selected_rows = st.session_state.selected_rows[
                ~st.session_state.selected_rows.index.isin(deselections)
            ]
        else:
            st.session_state.selected_rows = edited_df.loc[list(new_selections)].drop(columns=['Select'])
            
        st.session_state.previous_selection = current_selection

        if not st.session_state.selected_rows.empty:
            st.write("User Selected Records:")
            st.dataframe(st.session_state.selected_rows, hide_index=True)

    if st.session_state.show_awards and filters_applied:
        st.markdown("Fiscal Year 2025 NYC Government Procurement Awards")
        query = "SELECT * FROM nycproawards4"
        df_awards = pd.read_sql_query(query, conn)
        st.dataframe(df_awards, use_container_width=True)

        if st.session_state.show_matches and not st.session_state.selected_rows.empty and keyword:
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
    if not check_password():
        st.stop()
    main()
