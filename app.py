from flask import Flask, request, jsonify, abort

import firebase_admin
from firebase_admin import credentials, firestore, storage

path = 'college-gatekeeper-firebase-adminsdk-3ss20-fdf904afec.json'

cred = credentials.Certificate(path)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'college-gatekeeper.appspot.com'
})


# for base 64 encoding and decoding purposes
import base64

# for working with the directories
import os

# for processing the images
from PIL import Image, ImageOps, ImageEnhance

# image to text extractions
import pytesseract
from pytesseract import image_to_string

# regular expressions
import re 

# for current date time
import datetime

import requests

import io

app = Flask(__name__)

bucket = storage.bucket()

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        # getting the json data sent from the client side
        json_data = request.get_json()

        # adding the dead comment

        # accessing the base 64 encoded image string sent from the client side
        image_data = json_data['image']

        # decoding the base 64 encoded image string to binary format
        image_data = base64.b64decode(image_data)

        current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        image_path = os.path.join('images', f'{current_time}.jpg')

        blob = bucket.blob(image_path)
        blob.content_type = 'image/jpg'

        blob.upload_from_string(image_data, content_type=blob.content_type)

        signed_url = blob.generate_signed_url(
            version='v4',
            expiration=datetime.timedelta(days=7),  # Set the desired expiration time
            method='GET'
        )

        response = requests.get(signed_url)
        image_data = response.content

        image = Image.open(io.BytesIO(image_data))
        
        # saving the image data as jpg file by creating a new file
        # with open(image_path, 'wb') as f:
        #     f.write(image_data)

        # loading the image using PIL library
        # image = Image.open(image_path)

        # converting the image to its grayscale form
        # grayscale_image = ImageOps.grayscale(image)

        # replacing the original image by its grayscale form
        # image = grayscale_image

        # enhancer = ImageEnhance.Contrast(image)

        # factor = 1.5 #increase contrast
        # more_contrast_image = enhancer.enhance(factor)
        # more_contrast_image.save(image_path)

        # saving the grayscale image to the original image path
        # image.save(image_path)

        # extracting all the text from the image
        try:
            text = pytesseract.image_to_string(image)
        except:
            return jsonify({'message': 'library error'})

        # pattern to be matched:- starting with L, having two characters, and 7 digits
        pattern = r"[A-Z]{3}\d{7}"

        # searching for the pattern in the text
        match = re.search(pattern, text)

        # print(firestore.SERVER_TIMESTAMP.ToDateTime())

        # d = firestore.SERVER_TIMSETAMP.toDate()
        # print(d.toString())
        # print(text)

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
            # print(roll_number)  # Output: LCS2021005
        else:
            # print("Roll number not found.")
            roll_number = "Roll Number Not Found"
        
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

        day = int(datetime.datetime.now().strftime("%d"))
        hour = int(datetime.datetime.now().strftime("%H"))

        # if the sent roll number was correct
        if is_roll_number_confirm:
            db = firestore.client()

            # referring to the data collection with date document 
            collection_ref = db.collection('data').document(date).collection('entries')

            date_document_ref = db.collection('data').document(date)
            date_document_ref.set({
                'Server Timestamp': firestore.SERVER_TIMESTAMP,
            })

            # referring to the document with confirmed roll number
            search_roll_number_ref = collection_ref.document(roll_number)

            # getting the snapshot of the referred document
            search_roll_number_snapshot = search_roll_number_ref.get()

            # if the document already exists
            if search_roll_number_snapshot.exists:
                existing_document_data = search_roll_number_snapshot.to_dict()
                in_time_field = existing_document_data['In Time']
                out_time_field = existing_document_data['Out Time']
                if in_time_field == "-1":
                    updated_data = {
                        'Roll No': roll_number, 
                        'Out Time': out_time_field, 
                        'In Time': firestore.SERVER_TIMESTAMP,
                        'Server Timestamp': firestore.SERVER_TIMESTAMP,
                    }
                    search_roll_number_ref.set(updated_data)
                    out_time_field_string = str(out_time_field)
                    out_time_field_num = int(out_time_field_string[8:10])

                    # print(day != out_time_field_num or hour >= 13)

                    if day != out_time_field_num or hour >= 23:
                        defaulter_collection_ref = db.collection('defaulters')
                        defaulter_doc_ref = defaulter_collection_ref.document(roll_number)
                        defaulter_doc_ref.set({
                            'Server Timestamp': firestore.SERVER_TIMESTAMP,
                        })

                    return jsonify({'message': 'in-time recorded'})
                else:
                    updated_data = {
                        'Roll No': roll_number, 
                        'Out Time': firestore.SERVER_TIMESTAMP, 
                        'In Time': "-1",
                        'Server Timestamp': firestore.SERVER_TIMESTAMP,
                    }
                    search_roll_number_ref.set(updated_data)
                    return jsonify({'message': 'out-time recorded'})
            else:
                # else recording the data and inserting the document
                data = {
                    'Roll No': roll_number, 
                    'Out Time': firestore.SERVER_TIMESTAMP, 
                    'In Time': "-1",
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