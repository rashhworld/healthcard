import os
import random
import string
import shutil
import traceback
import PyPDF2
import fitz
import cv2
from pyzbar.pyzbar import decode
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_random_filename(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def crop_and_zoom_pdf(input_path, x=120, y=330, width=100, height=100, zoom_factor=350):
    random_filename = generate_random_filename() + ".pdf"
    output_path = os.path.join("output_files", random_filename)
    os.makedirs("output_files", exist_ok=True)

    with open(input_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page.cropbox.lower_left = (x, y)
            page.cropbox.upper_right = (x + width, y + height)
            page.scale(zoom_factor / 100, zoom_factor / 100)
            writer.add_page(page)

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

    return output_path


def pdf_to_png(pdf_path):
    random_folder_name = generate_random_filename()
    output_folder = os.path.join("output_images", random_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    pdf_document = fitz.open(pdf_path)

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        image_path = os.path.join(output_folder, f"page_{page_number + 1}.png")
        pix.save(image_path)

    pdf_document.close()

    return output_folder


def save_user_image(input_pdf):
    reader = PdfReader(input_pdf)
    page = reader.pages[0]
    count = 0

    for image_file_object in page.images:
        if count == 2:
            os.makedirs("user_images", exist_ok=True)

            random_filename = generate_random_filename() + ".png"
            user_image_path = os.path.join("user_images", random_filename)
            with open(user_image_path, "wb") as fp:
                fp.write(image_file_object.data)

                try:
                    user_image = cv2.imread(user_image_path)
                    aspect_ratio = user_image.shape[1] / user_image.shape[0]
                    resized_image = cv2.resize(user_image, (160, int(160 / aspect_ratio)))

                    cv2.imwrite(user_image_path, resized_image)
                except Exception as e:
                    traceback.print_exc()
            break
        count += 1

    return user_image_path


def decode_qr_code(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    qr_codes = decode(gray_image)

    if qr_codes:
        os.makedirs("qr_codes", exist_ok=True)

        qr_code_data = qr_codes[0].data.decode("utf-8")
        qr_code_data_list = [qr_code_data]

        x, y, w, h = qr_codes[0].rect
        qr_code_image = gray_image[y : y + h, x : x + w]
        qr_code_image_resized = cv2.resize(qr_code_image, (150, 150))
        random_filename = generate_random_filename() + ".png"
        qr_code_image_path = os.path.join("qr_codes", random_filename)

        cv2.imwrite(qr_code_image_path, qr_code_image_resized)

        return qr_code_image_path, qr_code_data_list


def merge_details_card(usrimg, qrimg, qrdata):
    background = Image.open("static/images/front.jpg")

    images = [
        {"path": usrimg, "x": 100, "y": 380},
        {"path": qrimg, "x": 1140, "y": 350},
    ]

    text_lines = qrdata[0].split("\n")
    positions = [
        {"text": text_lines[0], "x": 1100, "y": 664, "lable" : "PMJAY ID"},
        {"text": text_lines[1], "x": 270, "y": 664, "lable" : "ABHA No"},
        {"text": text_lines[2], "x": 310, "y": 360, "lable" : "Name"},
        {"text": text_lines[4], "x": 720, "y": 577, "lable" : "District"},
        {"text": text_lines[5], "x": 720, "y": 487, "lable" : "Village"},
        {"text": text_lines[6], "x": 720, "y": 532, "lable" : "Block"},
        {"text": text_lines[8], "x": 500, "y": 440, "lable" : "DOB"},
        {"text": text_lines[9], "x": 980, "y": 440, "lable" : "Gender"},
    ]

    font = ImageFont.truetype("arial.ttf", 20)
    draw = ImageDraw.Draw(background)

    for image_data in images:
        image = Image.open(image_data["path"])
        background.paste(image, (image_data["x"], image_data["y"]))

    for pos in positions:
        draw.text((pos["x"], pos["y"]), pos["text"], fill="black", font=font)

    os.makedirs("downloads", exist_ok=True)
    fileloc = "downloads/" + generate_random_filename() + ".jpg"
    background.save(fileloc)

    shutil.rmtree("output_files")
    shutil.rmtree("output_images")
    shutil.rmtree("user_images")
    shutil.rmtree("qr_codes")

    # background.show()

    return fileloc


def calculate_height(image_path, target_width):
    with Image.open(image_path) as img:
        aspect_ratio = img.width / img.height
        return target_width / aspect_ratio


def create_blank_pdf(images):
    output_pdf_path = "downloads/" + generate_random_filename() + ".pdf"
    target_width = 220
    y_position = 630

    c = canvas.Canvas(output_pdf_path, pagesize=letter)

    back_image_path = "static/images/back.jpg"
    back_image_height = calculate_height(back_image_path, target_width)

    for image_path in images:
        height = calculate_height(image_path, target_width)
        c.drawImage(image_path, 70, y_position, width=target_width, height=height)
        c.drawImage(back_image_path, 320, y_position, width=target_width, height=back_image_height)
        y_position -= height + 10

    c.save()

    return output_pdf_path
