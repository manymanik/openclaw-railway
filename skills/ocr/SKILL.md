# OCR - Extract Text from Scanned Documents

Use this skill when you encounter scanned PDFs or images that cannot be read directly.

## When to Use

- When a PDF appears to be image-based or scanned
- When you receive an error like "cannot read this PDF" or "image-based document"
- When the user asks to extract text from a scanned document or image

## How to Use

Run the Azure OCR tool using bash:

```bash
/app/mcp-venv/bin/python3 /app/src/mcp/azure_ocr.py "<file_path>"
```

Replace `<file_path>` with the absolute path to the PDF or image file.

## Supported Formats

- PDF files (`.pdf`)
- Images: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

## Example

If you receive a file at `/tmp/document.pdf` that appears to be scanned:

```bash
/app/mcp-venv/bin/python3 /app/src/mcp/azure_ocr.py "/tmp/document.pdf"
```

The tool will output the extracted text which you can then analyze and respond to.

## Notes

- Processing may take a few seconds per page
- The tool uses Azure Computer Vision for accurate OCR
- Works best with clearly scanned documents (not handwritten)
