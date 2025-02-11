import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import pandas as pd
import time
from io import BytesIO
import requests
from zipfile import ZipFile
import shutil
import os

@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = shutil.which("chromium-browser") or "/usr/bin/chromium-browser"

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options,
        )
        return driver
    except Exception as e:
        st.error(f"Error initializing WebDriver: {e}")
        return None

def scrape_nber():
    driver = get_driver()
    if driver is None:
        return None

    url = 'https://www.nber.org/papers?page=1&perPage=50&sortBy=public_date'
    try:
        driver.get(url)
        time.sleep(5)
        papers = driver.find_elements(By.CLASS_NAME, 'teaser')
    except Exception as e:
        st.error(f"Error accessing NBER site or finding elements: {e}")
        driver.quit()
        return None

    data = []
    for paper in papers:
        try:
            title_elem = paper.find_element(By.CLASS_NAME, 'title')
            title_text = title_elem.text.strip()

            author_elem = paper.find_element(By.CLASS_NAME, 'authors')
            authors = author_elem.text.strip()

            date_elem = paper.find_element(By.CLASS_NAME, 'date')
            date_text = date_elem.text.strip()

            link_elem = paper.find_element(By.TAG_NAME, 'a')
            link = link_elem.get_attribute('href')

            data.append({
                'Title': title_text,
                'Authors': authors,
                'Date': date_text,
                'Link': link
            })
        except Exception as e:
            st.warning(f"Error processing paper: {e}")
            continue

    driver.quit()
    return pd.DataFrame(data)

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='NBER Data')
    output.seek(0)
    return output

def download_pdfs(start, end):
    st.write("Starting to download PDFs...")
    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, 'w') as zip_file:
        for i in range(start, end + 1):
            url = f"https://www.nber.org/system/files/working_papers/w{i}/w{i}.pdf"
            response = requests.get(url)

            if response.status_code == 200:
                zip_file.writestr(f"w{i}.pdf", response.content)
            else:
                st.write(f"Failed to download: {url}")

    zip_buffer.seek(0)
    st.download_button(
        label="Download All PDFs as ZIP",
        data=zip_buffer,
        file_name="nber_papers.zip",
        mime="application/zip"
    )

    st.success("All PDFs have been downloaded successfully!")

st.title("NBER Paper Scraper and Downloader")
if st.button("Scrape NBER Data"):
    df = scrape_nber()
    if df is not None and not df.empty:
        st.success("Scraping completed successfully!")
        st.dataframe(df)
        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="Download Excel File", 
            data=excel_data, 
            file_name="nber_data.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No data scraped. Please verify the website structure.")

st.subheader("Download NBER PDFs")
start_range = st.text_input("Enter start range (e.g., 33405)", value="33405")
end_range = st.text_input("Enter end range (e.g., 33440)", value="33440")

if st.button("Download PDFs"):
    try:
        start_range = int(start_range)
        end_range = int(end_range)
        if start_range > 0 and end_range >= start_range:
            download_pdfs(start_range, end_range)
        else:
            st.error("Please enter valid positive numbers with the end range greater than or equal to the start range.")
    except ValueError:
        st.error("Please enter valid numerical values.")
