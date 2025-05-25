from app.services.pdf_service import PDFService
from io import BytesIO
from PyPDF2 import PdfReader
import requests


def validate_pdf(pdf_data: BytesIO) -> bool:
    """Validate if the data is a proper PDF"""
    try:
        pdf_data.seek(0)
        PdfReader(pdf_data)
        return True
    except Exception as e:
        print(f"PDF validation error: {str(e)}")
        return False


def test_merge_pdfs():
    # Initialize the service
    pdf_service = PDFService(is_prod=False)

    # Example presigned URLs (replace these with your actual presigned URLs)
    urls = ["htt"
    ]

    try:
        # Download PDFs
        pdf_files = []
        for i, url in enumerate(urls, 1):
            try:
                print(f"\nProcessing PDF {i}/{len(urls)}")
                print(f"Downloading from: {url}")

                # Download using requests first to check content type
                response = requests.get(url)
                response.raise_for_status()

                # Check if it's a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'application/pdf' not in content_type:
                    print(
                        f"Warning: URL {i} might not be a PDF (Content-Type: {content_type})")

                # Create BytesIO object
                pdf_data = BytesIO(response.content)

                # Validate PDF
                if not validate_pdf(pdf_data):
                    print(
                        f"Warning: URL {i} might be corrupted or not a valid PDF")
                    continue

                pdf_files.append(pdf_data)
                print(f"Successfully downloaded and validated PDF {i}")

            except Exception as e:
                print(f"Error processing URL {i}: {str(e)}")
                continue

        if not pdf_files:
            raise Exception("No valid PDFs were downloaded")

        print(f"\nSuccessfully downloaded {len(pdf_files)} PDFs")

        # Merge PDFs
        print("\nStarting PDF merge...")
        merged_pdf = pdf_service.merge_pdfs(pdf_files)
        print("Successfully merged PDFs!")

        # Save the merged PDF locally for verification
        output_path = "merged_output.pdf"
        with open(output_path, "wb") as f:
            f.write(merged_pdf.getvalue())
        print(f"Merged PDF saved as '{output_path}'")

        # Verify the merged PDF
        if validate_pdf(merged_pdf):
            print("Final merged PDF validation successful!")
        else:
            print("Warning: Final merged PDF validation failed!")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")


if __name__ == "__main__":
    test_merge_pdfs()
