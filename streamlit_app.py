import streamlit as st
import requests
from io import BytesIO
from zipfile import ZipFile

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

st.title("Download NBER PDFs")
start_range = st.number_input("Enter start range", min_value=1, value=32500)
end_range = st.number_input("Enter end range", min_value=start_range, value=32510)

if st.button("Download PDFs"):
    download_pdfs(start_range, end_range)
