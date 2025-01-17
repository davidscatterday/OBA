import streamlit as st

st.set_page_config(layout="wide")  # Set the page layout to wide

import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

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
                fiscal_quarter, job_titles, headcount
            )
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
                use_container_width=True  # Make the table use the full width
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

# Function to scrape data from the website
def scrape_data():
    cookies = {
        'ak_bmsc': '0E08843E4257240434F033A03D6714DD~000000000000000000000000000000~YAAQSJ42F2yUkS+TAQAAc5QEQBk6tyeodmKbK0+6Uz4uJ6d/3sUD6zZEk5sfq+ZaP84RgD+ji4onlCBFYFbPm1iycFE72h894XCCgh0ZiTRMWZZ/1Yg9WVZfeyFNfvkR6mg3zLN9nSOfADBrWbtFfvP1bfyiB5Rzqywa88H1NTeX2qvUsS9B9IAiTiRPav/KfjSEuSYEioe4jl6pG14gNkwyjK6FAKUJkQX64e3Q9RVFC+plwrylg+Sg89pWKkt0ED/H9gTMe7s6ix9IyQuYrB7Mdu2QKXDogTeTQTH7C+deNFiHQwcy2c3Sj7iB5mIP8dIRWi2Z2a9YwKksra6mtcu51Zg+BeqaY4rEwy6tS65hmF7yfTCJpw5nUn54Ev4=',
        '_ga': 'GA1.2.1749921805.1731945974',
        '_gid': 'GA1.2.739001020.1731945974',
        '_gat': '1',
        '_ga_KFWPDKF16D': 'GS1.2.1731945975.1.1.1731947398.0.0.0',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        # 'cookie': 'ak_bmsc=0E08843E4257240434F033A03D6714DD~000000000000000000000000000000~YAAQSJ42F2yUkS+TAQAAc5QEQBk6tyeodmKbK0+6Uz4uJ6d/3sUD6zZEk5sfq+ZaP84RgD+ji4onlCBFYFbPm1iycFE72h894XCCgh0ZiTRMWZZ/1Yg9WVZfeyFNfvkR6mg3zLN9nSOfADBrWbtFfvP1bfyiB5Rzqywa88H1NTeX2qvUsS9B9IAiTiRPav/KfjSEuSYEioe4jl6pG14gNkwyjK6FAKUJkQX64e3Q9RVFC+plwrylg+Sg89pWKkt0ED/H9gTMe7s6ix9IyQuYrB7Mdu2QKXDogTeTQTH7C+deNFiHQwcy2c3Sj7iB5mIP8dIRWi2Z2a9YwKksra6mtcu51Zg+BeqaY4rEwy6tS65hmF7yfTCJpw5nUn54Ev4=; _ga=GA1.2.1749921805.1731945974; _gid=GA1.2.739001020.1731945974; _gat=1; _ga_KFWPDKF16D=GS1.2.1731945975.1.1.1731947398.0.0.0',
        'origin': 'https://a856-cityrecord.nyc.gov',
        'priority': 'u=0, i',
        'referer': 'https://a856-cityrecord.nyc.gov/Section',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    }
    data_data = []
    for i in range(1,5):
        data = {
            'SectionId': '6',
            'SectionName': '\r\n                                                \r\n                                                    \r\n                                                \r\n                                                Procurement\r\n                                            ',
            'NoticeTypeId': '0',
            'PageNumber': f'{i}',
        }

        response = requests.post('https://a856-cityrecord.nyc.gov/Section', cookies=cookies, headers=headers, data=data)

        # test = scrapy.Selector(text=response.text)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all div elements with class 'notice-item'
        notice_items = soup.find_all('div', class_='notice-container')


        for item in notice_items:
            # Extract text from various fields
            # Extract the title
            title = item.find('h1').text.strip()

            # Extract the agency
            agency = item.find('strong').text.strip()

            #Extract the Award Date
            award_date = item.find_all('small')[-1].text.strip().split('\n')[-1].strip()

            # Extract the category
            category = item.find('i', class_='fa fa-tag').next_sibling.strip()

            # Extract the description
            description = item.find('p', class_='short-description').text.strip()

            data_data.append({
                'Agency': agency,
                'Title': title,
                'Award Date': award_date,
                'Description': description,
                'Category': category
            })

    return pd.DataFrame(data_data)


# Streamlit app
st.title('NYC City Record Scraper')
#
url = 'https://a856-cityrecord.nyc.gov/Section'
st.write(f"Scraping data from: {url}")
# render dataframe table
if st.button('Scrape Data'):
    df = scrape_data()
    if df is not None:  # Check if df is not None before proceeding
        st.write(f"Total records scraped: {len(df)}")
        st.dataframe(df, use_container_width=True)  # Set use_container_width to True
    else:
        st.write("No data was scraped.")
