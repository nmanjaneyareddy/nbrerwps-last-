import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
from io import BytesIO
from zipfile import ZipFile

@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_nber(start, end):
    nber_web_frame = pd.DataFrame(columns=['Title', 'Author', 'Issue_date', 'WP_NO', 'DOI'])
    driver = get_driver()

    for i in range(start, end + 1):
        try:
            driver.get(f'https://www.nber.org/papers/w{i}')
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            title_tag = soup.find('h1', class_='page-header__title')
            author_tag = soup.find('div', class_='page-header__authors')
            wp_no_tag = soup.find('div', class_='page-header__citation-item')
            doi_tag = soup.find_all('div', class_='page-header__citation-item')
            issue_date_tag = soup.find('time', {'datetime': True})

            title = title_tag.text.strip() if title_tag else 'N/A'
            author = author_tag.text.replace('\n', '').strip().replace('&', ',').replace('  ', '') if author_tag else 'N/A'
            wp_no = wp_no_tag.span.string.strip() if wp_no_tag and wp_no_tag.span else 'N/A'
            doi = doi_tag[1].span.string.strip() if len(doi_tag) > 1 and doi_tag[1].span else 'N/A'
            issue_date = issue_date_tag['datetime'] if issue_date_tag else 'N/A'

            new_row = pd.DataFrame({
                'Title': [title],
                'Author': [author],
                'Issue_date': [issue_date],
                'WP_NO': [wp_no],
                'DOI': [doi]
            })

            nber_web_frame = pd.concat([nber_web_frame, new_row], ignore_index=True)

        except Exception as e:
            st.warning(f"Error processing paper w{i}: {e}")

    driver.quit()
    return nber_web_frame

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

st.title("NBER Paper Scraper")
start_range = st.number_input("Enter start range", min_value=1, value=32500)
end_range = st.number_input("Enter end range", min_value=start_range, value=32510)

if st.button("Scrape NBER Data"):
    df = scrape_nber(start_range, end_range)
    if not df.empty:
        st.success("Scraping completed successfully!")
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "nber_data.csv", "text/csv")
    else:
        st.warning("No data scraped. Please verify the website structure.")

if st.button("Download PDFs"):
    download_pdfs(start_range, end_range)
