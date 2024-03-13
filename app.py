from flask import Flask, render_template, request, send_file
from script import *

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    files = [request.files[f"file{i}"] for i in range(1, 6) if f"file{i}" in request.files]
    processed_pdfs = []

    for file in files:
        if file:
            if (file.filename != "" and file.filename.endswith(".pdf") and file.content_length < 3 * 1024 * 1024):
                os.makedirs("uploads", exist_ok=True)

                filename = generate_random_filename() + ".pdf"
                filepath = os.path.join("uploads", filename)
                file.save(filepath)
                result_path = process_pdf(filepath)
                processed_pdfs.append(result_path)
            else:
                return "Invalid file. File must be a PDF and should be less than 3MB in size."

    if processed_pdfs:
        output_pdf_path = create_blank_pdf(processed_pdfs)
        return send_file(output_pdf_path, as_attachment=True)
    else:
        return "No valid PDF files were provided."


def process_pdf(filepath):
    cropped_pdf = crop_and_zoom_pdf(filepath)
    cropped_images = pdf_to_png(cropped_pdf)
    image_path = os.path.join(cropped_images, os.listdir(cropped_images)[0])
    user_image_path = save_user_image(filepath)
    qr_img, qr_data = decode_qr_code(image_path)
    result_path = merge_details_card(user_image_path, qr_img, qr_data)
    return result_path
