import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Function to scrape data from the website
def scrape_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all div elements with class 'notice-item'
    notice_items = soup.find_all('div', class_='notice-item')
    
    data = []
    for item in notice_items:
        # Extract text from various fields
        agency = item.find('div', class_='agency').text.strip()
        title = item.find('div', class_='title').text.strip()
        description = item.find('div', class_='description').text.strip()
        category = item.find('div', class_='category').text.strip()
        
        data.append({
            'Agency': agency,
            'Title': title,
            'Description': description,
            'Category': category
        })
    
    return pd.DataFrame(data)

# Streamlit app
st.title('NYC City Record Scraper')

url = 'https://a856-cityrecord.nyc.gov/Section'
st.write(f"Scraping data from: {url}")

if st.button('Scrape Data'):
    df = scrape_data(url)
    st.write(f"Total records scraped: {len(df)}")
    st.dataframe(df)

    # Optional: Download CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="nyc_city_record_data.csv",
        mime="text/csv",
    )