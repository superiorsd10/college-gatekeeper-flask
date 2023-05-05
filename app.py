from flask import Flask, request, jsonify, abort

# for base 64 encoding and decoding purposes
import base64

# for working with the directories
import os

# for processing the images
from PIL import Image, ImageOps, ImageEnhance

# image to text extractions
import pytesseract

# regular expressions
import re 

# for current date time
import datetime

app = Flask(__name__)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        # getting the json data sent from the client side
        json_data = request.get_json()

        # accessing the base 64 encoded image string sent from the client side
        image_data = json_data['image']

        # decoding the base 64 encoded image string to binary format
        image_data = base64.b64decode(image_data)

        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        image_path = os.path.join('images', f'{current_time}.jpg')
        
        # saving the image data as jpg file by creating a new file
        with open(image_path, 'wb') as f:
            f.write(image_data)

        # loading the image using PIL library
        image = Image.open(image_path)

        # converting the image to its grayscale form
        grayscale_image = ImageOps.grayscale(image)

        # replacing the original image by its grayscale form
        image = grayscale_image

        enhancer = ImageEnhance.Contrast(image)

        factor = 1.5 #increase contrast
        more_contrast_image = enhancer.enhance(factor)
        more_contrast_image.save(image_path)

        # saving the grayscale image to the original image path
        # image.save(image_path)

        # extracting all the text from the image
        text = pytesseract.image_to_string(image)

        # pattern to be matched:- starting with L, having two characters, and 7 digits
        pattern = r"\w{3}\d{7}"

        # searching for the pattern in the text
        match = re.search(pattern, text)

        print(text)

        # if matched, assigning the roll number
        if match:
            roll_number = match.group()
            print(roll_number)  # Output: LCS2021005
        else:
            print("Roll number not found.")
            roll_number = -1
        
        # senting the roll number to client side in the form of json object
        return jsonify({'message': roll_number})
    except KeyError:
        abort(400, 'Invalid request body')
    except:
        abort(500, 'Internal server error')