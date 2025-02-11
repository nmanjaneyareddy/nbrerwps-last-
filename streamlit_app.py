import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
from io import BytesIO
import requests


def get_downloads_path():
    # Cross-platform Downloads folder detection
    try:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            raise FileNotFoundError("Downloads path not found.")
        return downloads
    except Exception as e:
        st.warning(f"Error locating Downloads path: {e}")
        return os.getcwd()  # Fallback to current directory


def scrape_nber():
    # Set up Selenium with headless option
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.binary_location = '/usr/bin/chromium-browser'  # Explicit path for Streamlit Cloud

    try:
        # Set up the WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        st.error(f"Error initializing WebDriver: {e}")
        return None

    url = 'https://www.nber.org/papers?page=1&perPage=50&sortBy=public_date'
    driver.get(url)

    # Allow time for the page to load
    time.sleep(5)

    try:
        papers = driver.find_elements(By.CLASS_NAME, 'teaser')
    except Exception as e:
        st.error(f"Error finding elements: {e}")
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

    df = pd.DataFrame(data)
    return df


def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='NBER Data')
    output.seek(0)
    return output


def download_pdfs(start, end):
    # Save PDFs to the user's Downloads folder (or fallback directory)
    downloads_path = os.path.join(get_downloads_path(), "NBER_Papers")
    os.makedirs(downloads_path, exist_ok=True)

    st.write(f"Starting to download PDFs to {downloads_path}...")
    for i in range(start, end + 1):
        url = f"https://www.nber.org/system/files/working_papers/w{i}/w{i}.pdf"
        response = requests.get(url)

        if response.status_code == 200:
            filename = os.path.join(downloads_path, url.split('/')[-1])
            with open(filename, 'wb') as out_file:
                out_file.write(response.content)
            st.write(f"Downloaded: {filename}")
        else:
            st.write(f"Failed to download: {url}")
    st.success(f"Download complete! Files saved to: {downloads_path}")


st.title("NBER Paper Scraper and Downloader")
if st.button("Scrape NBER Data"):
    df = scrape_nber()
    if df is not None and not df.empty:
        st.success("Scraping completed successfully!")
        st.dataframe(df)
        excel_data = convert_df_to_excel(df)
        st.download_button(label="Download Excel File", data=excel_data, file_name="nber_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
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
