import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
import os

def scrape_nber():
    url = 'https://www.nber.org/papers?page=1&perPage=50&sortBy=public_date#listing-77041'
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error("Failed to retrieve data. Check the URL or try again later.")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Debugging output
    st.write("Page fetched successfully.")

    # Adjusted selector based on possible website structure changes
    results = soup.find_all('div', class_='digest-card')
    if not results:
        st.error("No data found. The structure of the website may have changed.")
        return None
    
    data = []
    
    for job_elem in results:
        title_elem = job_elem.find('h3', class_='digest-card__title')
        year_elem = job_elem.find('span', class_="digest-card__label")
        wpno_elem = job_elem.find('a', class_='paper-card__paper_number')
        auth_elem = job_elem.find('p', class_='digest-card__items')

        st.write(f"Processing: {title_elem}, {year_elem}, {wpno_elem}, {auth_elem}")

        if not all([title_elem, year_elem, wpno_elem, auth_elem]):
            continue

        title_text = title_elem.text.strip()
        year = year_elem.text.strip() if year_elem else ''
        WpNo = wpno_elem.text.strip()
        auth1 = auth_elem.text.strip().replace('Author(s) - ', '') if auth_elem else ''

        data.append({
            'Source': 'National Bureau of Economic Research',
            'Title': title_text,
            'Year': year,
            'WP_NO': WpNo,
            'Place': 'Cambridge',
            'Publisher': 'NBER',
            'Series': 'NBER Working Papers ;',
            'wpno': 'NBERWP ' + WpNo,
            'Author': auth1
        })

    df = pd.DataFrame(data)

    # Safely split 'Title' into 'Title1' and 'Subtitle'
    def safe_split(row):
        parts = row['Title'].split(':', maxsplit=1)
        return pd.Series(parts if len(parts) == 2 else [parts[0], ''], index=['Title1', 'Subtitle'])

    if 'Title' in df.columns:
        split_titles = df.apply(safe_split, axis=1)
        df = pd.concat([df, split_titles], axis=1)
        df.drop('Title', axis=1, inplace=True)

    return df

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='NBER Data')
    output.seek(0)
    return output

def download_pdfs(start, end):
    folder_location = "NBER_Papers"
    os.makedirs(folder_location, exist_ok=True)

    st.write("Starting to download PDFs...")
    for i in range(start, end + 1):
        url = f"https://www.nber.org/system/files/working_papers/w{i}/w{i}.pdf"
        response = requests.get(url)

        if response.status_code == 200:
            filename = os.path.join(folder_location, url.split('/')[-1])
            with open(filename, 'wb') as out_file:
                out_file.write(response.content)
            st.write(f"Downloaded: {filename}")
        else:
            st.write(f"Failed to download: {url}")
    st.success("Download complete!")

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
