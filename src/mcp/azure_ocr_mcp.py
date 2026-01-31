#!/usr/bin/env python3
"""
Azure Vision OCR MCP Server for OpenClaw
Preprocesses scanned PDFs and images using Azure Computer Vision OCR.
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
from pathlib import Path

# Azure SDK
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

# PDF processing
import fitz  # PyMuPDF for PDF handling

# MCP protocol
import struct

AZURE_ENDPOINT = os.environ.get("AZURE_VISION_ENDPOINT", "https://manik-comp-vision12314.cognitiveservices.azure.com/")
AZURE_KEY = os.environ.get("AZURE_VISION_KEY", "")

def get_vision_client():
    """Create Azure Computer Vision client."""
    if not AZURE_KEY:
        raise ValueError("AZURE_VISION_KEY environment variable not set")
    return ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))

def extract_text_from_image(client, image_bytes):
    """Extract text from image bytes using Azure OCR."""
    import io
    stream = io.BytesIO(image_bytes)

    # Call the Read API
    read_response = client.read_in_stream(stream, raw=True)

    # Get operation location
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Wait for result
    while True:
        result = client.get_read_result(operation_id)
        if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
            break
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.5))

    # Extract text
    text_results = []
    if result.status == OperationStatusCodes.succeeded:
        for page in result.analyze_result.read_results:
            for line in page.lines:
                text_results.append(line.text)

    return "\n".join(text_results)

def process_pdf(pdf_path):
    """Convert PDF pages to images and OCR each page."""
    client = get_vision_client()
    doc = fitz.open(pdf_path)

    all_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page to image at 300 DPI for better OCR
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")

        page_text = extract_text_from_image(client, img_bytes)
        all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")

    doc.close()
    return "\n\n".join(all_text)

def process_image(image_path):
    """OCR a single image file."""
    client = get_vision_client()
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    return extract_text_from_image(client, img_bytes)

def process_base64_image(b64_data, mime_type="image/png"):
    """OCR base64-encoded image data."""
    client = get_vision_client()
    img_bytes = base64.b64decode(b64_data)
    return extract_text_from_image(client, img_bytes)

def process_base64_pdf(b64_data):
    """OCR base64-encoded PDF data."""
    pdf_bytes = base64.b64decode(b64_data)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        return process_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)

# MCP Protocol Implementation
def read_message():
    """Read a JSON-RPC message from stdin."""
    # Read Content-Length header
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line or line == b'\r\n' or line == b'\n':
            break
        if b':' in line:
            key, value = line.decode('utf-8').strip().split(':', 1)
            headers[key.strip().lower()] = value.strip()

    content_length = int(headers.get('content-length', 0))
    if content_length == 0:
        return None

    content = sys.stdin.buffer.read(content_length)
    return json.loads(content.decode('utf-8'))

def write_message(msg):
    """Write a JSON-RPC message to stdout."""
    content = json.dumps(msg)
    content_bytes = content.encode('utf-8')
    header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
    sys.stdout.buffer.write(header.encode('utf-8'))
    sys.stdout.buffer.write(content_bytes)
    sys.stdout.buffer.flush()

def handle_initialize(msg):
    """Handle initialize request."""
    return {
        "jsonrpc": "2.0",
        "id": msg["id"],
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "azure-ocr",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }
    }

def handle_tools_list(msg):
    """Handle tools/list request."""
    return {
        "jsonrpc": "2.0",
        "id": msg["id"],
        "result": {
            "tools": [
                {
                    "name": "ocr_file",
                    "description": "Extract text from a scanned PDF or image file using Azure Computer Vision OCR. Use this for documents that appear to be scanned/image-based and cannot be read directly.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the PDF or image file to OCR"
                            }
                        },
                        "required": ["file_path"]
                    }
                },
                {
                    "name": "ocr_base64",
                    "description": "Extract text from base64-encoded PDF or image data using Azure Computer Vision OCR.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "Base64-encoded file content"
                            },
                            "file_type": {
                                "type": "string",
                                "enum": ["pdf", "image"],
                                "description": "Type of file: 'pdf' or 'image'"
                            }
                        },
                        "required": ["data", "file_type"]
                    }
                }
            ]
        }
    }

def handle_tools_call(msg):
    """Handle tools/call request."""
    params = msg.get("params", {})
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "ocr_file":
            file_path = arguments.get("file_path")
            if not file_path:
                raise ValueError("file_path is required")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            suffix = path.suffix.lower()
            if suffix == ".pdf":
                text = process_pdf(file_path)
            elif suffix in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"]:
                text = process_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

            return {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"OCR extracted text from {path.name}:\n\n{text}"
                        }
                    ]
                }
            }

        elif tool_name == "ocr_base64":
            data = arguments.get("data")
            file_type = arguments.get("file_type")

            if not data:
                raise ValueError("data is required")
            if not file_type:
                raise ValueError("file_type is required")

            if file_type == "pdf":
                text = process_base64_pdf(data)
            else:
                text = process_base64_image(data)

            return {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"OCR extracted text:\n\n{text}"
                        }
                    ]
                }
            }

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }
        }

def main():
    """Main MCP server loop."""
    while True:
        try:
            msg = read_message()
            if msg is None:
                break

            method = msg.get("method", "")

            if method == "initialize":
                response = handle_initialize(msg)
            elif method == "initialized":
                continue  # No response needed
            elif method == "tools/list":
                response = handle_tools_list(msg)
            elif method == "tools/call":
                response = handle_tools_call(msg)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            if msg.get("id") is not None:
                write_message(response)

        except Exception as e:
            sys.stderr.write(f"MCP Server Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
