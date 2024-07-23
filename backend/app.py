from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import os
import uuid

app = Flask(__name__)
CORS(app)

# Create a temporary directory for file uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the file to the uploads folder
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    
    # Convert PDF to HTML
    html_content = pdf_to_html(file_path)
    
    # Save the HTML file
    html_filename = os.path.splitext(unique_filename)[0] + '.html'
    html_path = os.path.join(UPLOAD_FOLDER, html_filename)
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    # Clean up the uploaded file
    os.remove(file_path)
    
    return jsonify({'htmlPath': html_path, 'htmlContent': html_content})

def pdf_to_html(pdf_path):
    doc = fitz.open(pdf_path)
    html_content = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .page {
                position: relative;
                width: 595px;
                height: 842px;
                margin: 20px auto;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                border: 1px solid #ccc;
                background: white;
                overflow: hidden;
            }
            .text {
                position: absolute;
                white-space: pre;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                position: absolute;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }
            .rect {
                position: absolute;
                box-sizing: border-box;
            }
        </style>
    </head>
    <body>
    """

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        html_content += f'<div class="page">'

        # Extract text with layout
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_flags = span["flags"]
                        font_weight = "bold" if (font_flags & 2) or ("Bold" in span["font"]) else "normal"
                        font_style = "italic" if (font_flags & 1) or ("Italic" in span["font"] or "Oblique" in span["font"]) else "normal"
                        style = (f'left: {span["bbox"][0]}px; top: {span["bbox"][1]}px; '
                                 f'font-size: {span["size"]}px; font-family: {span["font"]}; '
                                 f'font-weight: {font_weight}; font-style: {font_style}; '
                                 f'color: rgb({span["color"] & 255}, '
                                 f'{(span["color"] >> 8) & 255}, '
                                 f'{(span["color"] >> 16) & 255});')
                        html_content += f'<span class="text" style="{style}">{span["text"].replace(" ", "&nbsp;")}</span>'

        # Extract and draw table borders
        shapes = page.get_drawings()
        for shape in shapes:
            if shape["type"] == "rect":
                bbox = shape["rect"]
                border_width = shape.get("width", 1)  # Default to 1 if no border width
                border_color = shape.get("color", 0)  # Default to black if no border color
                border_rgb = f'rgb({border_color & 255}, {(border_color >> 8) & 255}, {(border_color >> 16) & 255})'
                style = (f'left: {bbox[0]}px; top: {bbox[1]}px; '
                         f'width: {bbox[2] - bbox[0]}px; height: {bbox[3] - bbox[1]}px; '
                         f'border: {border_width}px solid {border_rgb};')
                html_content += f'<div class="rect" style="{style}"></div>'

        html_content += '</div>'

    html_content += "</body></html>"
    return html_content

if __name__ == '__main__':
    app.run(debug=True)
