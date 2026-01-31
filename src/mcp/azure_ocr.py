#!/usr/bin/env python3
"""
Azure Vision OCR CLI Tool
Extract text from scanned PDFs and images using Azure Computer Vision.

Usage:
  python3 azure_ocr.py <file_path>
  python3 azure_ocr.py --base64 <base64_data> --type pdf|image

Environment Variables:
  AZURE_VISION_KEY      - Azure Computer Vision API key
  AZURE_VISION_ENDPOINT - Azure Computer Vision endpoint URL
"""

import sys
import os
import base64
import tempfile
import time
import argparse

def get_vision_client():
    """Create Azure Computer Vision client."""
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from msrest.authentication import CognitiveServicesCredentials

    endpoint = os.environ.get("AZURE_VISION_ENDPOINT", "")
    key = os.environ.get("AZURE_VISION_KEY", "")

    if not endpoint or not key:
        print("Error: AZURE_VISION_KEY and AZURE_VISION_ENDPOINT environment variables must be set", file=sys.stderr)
        sys.exit(1)

    return ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))

def extract_text_from_image(client, image_bytes):
    """Extract text from image bytes using Azure OCR."""
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    import io

    stream = io.BytesIO(image_bytes)

    # Call the Read API
    read_response = client.read_in_stream(stream, raw=True)

    # Get operation location
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Wait for result (with timeout)
    max_wait = 60  # seconds
    waited = 0
    while waited < max_wait:
        result = client.get_read_result(operation_id)
        if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
            break
        time.sleep(0.5)
        waited += 0.5

    if result.status != OperationStatusCodes.succeeded:
        print(f"Error: OCR operation failed with status: {result.status}", file=sys.stderr)
        return ""

    # Extract text
    text_results = []
    for page in result.analyze_result.read_results:
        for line in page.lines:
            text_results.append(line.text)

    return "\n".join(text_results)

def process_pdf(pdf_path):
    """Convert PDF pages to images and OCR each page."""
    import fitz  # PyMuPDF

    client = get_vision_client()
    doc = fitz.open(pdf_path)

    all_text = []
    total_pages = len(doc)

    for page_num in range(total_pages):
        print(f"Processing page {page_num + 1}/{total_pages}...", file=sys.stderr)
        page = doc[page_num]

        # Render page to image at 300 DPI for better OCR
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")

        page_text = extract_text_from_image(client, img_bytes)
        if page_text:
            all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")

        # Rate limit: wait 3 seconds between pages to avoid Azure throttling
        if page_num < total_pages - 1:
            time.sleep(3)

    doc.close()
    return "\n\n".join(all_text)

def process_image(image_path):
    """OCR a single image file."""
    client = get_vision_client()
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    return extract_text_from_image(client, img_bytes)

def main():
    parser = argparse.ArgumentParser(description="Extract text from scanned PDFs and images using Azure OCR")
    parser.add_argument("file_path", nargs="?", help="Path to PDF or image file")
    parser.add_argument("--base64", dest="b64_data", help="Base64-encoded file data (instead of file path)")
    parser.add_argument("--type", dest="file_type", choices=["pdf", "image"], help="File type when using --base64")

    args = parser.parse_args()

    if args.b64_data:
        if not args.file_type:
            print("Error: --type is required when using --base64", file=sys.stderr)
            sys.exit(1)

        file_bytes = base64.b64decode(args.b64_data)

        if args.file_type == "pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                text = process_pdf(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            text = extract_text_from_image(get_vision_client(), file_bytes)

    elif args.file_path:
        if not os.path.exists(args.file_path):
            print(f"Error: File not found: {args.file_path}", file=sys.stderr)
            sys.exit(1)

        ext = os.path.splitext(args.file_path)[1].lower()

        if ext == ".pdf":
            text = process_pdf(args.file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"]:
            text = process_image(args.file_path)
        else:
            print(f"Error: Unsupported file type: {ext}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)

    # Output the extracted text
    print(text)

if __name__ == "__main__":
    main()
