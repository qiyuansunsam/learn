# file_handler.py
import os
from pathlib import Path
# Consider using pypdf: pip install pypdf
try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    PDF_LIB_AVAILABLE = True
except ImportError:
    print("Warning: pypdf not found. PDF reading functionality will be disabled.")
    print("Install it using: pip install pypdf")
    PDF_LIB_AVAILABLE = False

def read_text_files_in_folder(folder_path_str: str) -> str:
    """Reads and concatenates text from all .txt files in a folder."""
    all_text = ""
    folder_path = Path(folder_path_str)
    if not folder_path.is_dir():
        print(f"Warning: Directory not found: {folder_path_str}")
        return ""

    print(f"Reading text files from: {folder_path}")
    for txt_file in folder_path.glob('*.txt'):
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_text += content + "\n\n--- End of File: " + txt_file.name + " ---\n\n"
            print(f"  Read: {txt_file.name}")
        except Exception as e:
            print(f"  Error reading {txt_file.name}: {e}")
    return all_text

def read_pdfs_in_folder(folder_path_str: str) -> str:
    """Reads text content from all PDF files within a specified folder using pypdf."""
    if not PDF_LIB_AVAILABLE:
        print("Error: PDF library (pypdf) not available.")
        return ""

    all_text = ""
    folder_path = Path(folder_path_str)

    if not folder_path.is_dir():
        print(f"Error: Directory not found at {folder_path_str}")
        return ""

    print(f"Reading PDF files from: {folder_path}")
    pdf_files = list(folder_path.glob('*.pdf'))

    if not pdf_files:
        print(f"No PDF files found in {folder_path_str}")
        return ""

    for pdf_file in pdf_files:
        try:
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)
            print(f"  Reading {pdf_file.name} ({num_pages} pages)...")
            file_text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    file_text += page_text + "\n"
            if file_text:
                 all_text += file_text + "\n--- End of Document: " + pdf_file.name + " ---\n\n"
        except PdfReadError:
            print(f"  Warning: Could not read corrupted or encrypted PDF: {pdf_file.name}")
        except Exception as e:
            print(f"  Error reading {pdf_file.name}: {e}")

    print(f"Finished reading {len(pdf_files)} PDF file(s).")
    return all_text
