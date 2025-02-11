import streamlit as st
import requests
from io import BytesIO
from zipfile import ZipFile
from PyPDF2 import PdfReader
import pandas as pd

def download_pdfs_and_generate_report(start, end):
    st.write("Starting to download PDFs...")
    zip_buffer = BytesIO()
    pdf_info = []

    with ZipFile(zip_buffer, 'w') as zip_file:
        for i in range(start, end + 1):
            url = f"https://www.nber.org/system/files/working_papers/w{i}/w{i}.pdf"
            response = requests.get(url)

            if response.status_code == 200:
                pdf_name = f"w{i}.pdf"
                zip_file.writestr(pdf_name, response.content)

                # Count the number of pages in the PDF
                pdf_reader = PdfReader(BytesIO(response.content))
                num_pages = len(pdf_reader.pages)

                # Store the PDF name and page count
                pdf_info.append({'File Name': pdf_name, 'Number of Pages': num_pages})
            else:
                st.write(f"Failed to download: {url}")

    zip_buffer.seek(0)

    # Create a DataFrame with the PDF information
    df = pd.DataFrame(pdf_info)

    # Write the DataFrame to an Excel file
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='PDF Page Counts')
    excel_buffer.seek(0)

    # Provide download buttons for the ZIP and Excel files
    st.download_button(
        label="Download All PDFs as ZIP",
        data=zip_buffer,
        file_name="nber_papers.zip",
        mime="application/zip"
    )

    st.download_button(
        label="Download PDF Page Counts as Excel",
        data=excel_buffer,
        file_name="pdf_page_counts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("PDFs have been downloaded and the report has been generated successfully!")

st.title("NBER Paper Downloader and Page Counter")

st.subheader("Download NBER PDFs and Generate Page Count Report")
start_range = st.text_input("Enter start range (e.g., 33405)", value="33405")
end_range = st.text_input("Enter end range (e.g., 33440)", value="33440")

if st.button("Download PDFs and Generate Report"):
    try:
        start_range = int(start_range)
        end_range = int(end_range)
        if start_range > 0 and end_range >= start_range:
            download_pdfs_and_generate_report(start_range, end_range)
        else:
            st.error("Please enter valid positive numbers with the end range greater than or equal to the start range.")
    except ValueError:
        st.error("Please enter valid numerical values.")
