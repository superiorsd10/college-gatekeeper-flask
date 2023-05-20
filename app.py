from flask import Flask, request, jsonify, abort

import firebase_admin
from firebase_admin import credentials, firestore

path = '/Users/sachin/Desktop/Python Academics/College GateKeeper/college-gatekeeper-flask/college-gatekeeper-firebase-adminsdk-3ss20-fdf904afec.json'

cred = credentials.Certificate(path)
firebase_admin.initialize_app(cred)


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
            roll_number_branch = roll_number[0:3]
            is_found_dollar = roll_number_branch.find("$")
            if is_found_dollar:
                roll_number.replace("$", "S")
            is_found_one = roll_number_branch.find("1")
            if is_found_one:
                roll_number.replace("1", "I")
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


@app.route('/confirm_roll_number', methods=['POST'])
def confirm_roll_number():
    try:
        # getting the json data from the client side after confirming the roll number
        json_data = request.get_json()

        # accessing the confirm roll_number field
        is_roll_number_confirm = json_data['confirm']

        # accessing the roll number 
        roll_number = json_data['roll_number']

        # recording the current date
        date = datetime.datetime.now().strftime("%d-%m-%y")

        # if the sent roll number was correct
        if is_roll_number_confirm:
            db = firestore.client()

            # referring to the data collection with date document 
            collection_ref = db.collection('data').document(date).collection('entries')

            # referring to the document with confirmed roll number
            search_roll_number_ref = collection_ref.document(roll_number)

            # getting the snapshot of the referred document
            search_roll_number_snapshot = search_roll_number_ref.get()

            # if the document already exists
            if search_roll_number_snapshot.exists:

                # deleting the document and returning the json response
                search_roll_number_ref.delete()
                return jsonify({'message': 'in-time recorded'})
            else:

                # else recording the data and inserting the document
                data = {
                    'Roll No': roll_number, 
                    'In Time': firestore.SERVER_TIMESTAMP, 
                    'Server Timestamp': firestore.SERVER_TIMESTAMP,
                }
                doc_ref = collection_ref.document(roll_number)
                doc_ref.set(data)
                return jsonify({'message': 'out-time recorded'})
    except KeyError:
        abort(400, 'Invalid request body')
    except:
        abort(500, 'Internal server error')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)