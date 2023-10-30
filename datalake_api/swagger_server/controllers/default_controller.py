import connexion
import six

from swagger_server.models.asset import Asset  # noqa: E501
from swagger_server import util
from werkzeug.datastructures import FileStorage

import os
from flask import send_file, request
import json
from pymongo import MongoClient

import base64
import connexion
import six

from swagger_server.models.update_path_body import UpdatePathBody  # noqa: E501
from swagger_server import util


def delete_file(file_path):
    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['local']
    collection = db['metadata']
    
    try:
        # Check if the received path is an absolute path or relative to the current working directory
        if os.path.isabs(file_path):
            absolute_path = file_path
        else:
            absolute_path = os.path.join(os.getcwd(), file_path)
        # Debug print: Output the absolute_path
        print(f"Debug: absolute_path = {absolute_path}")
        
        # Create a JSON-like object for MongoDB query
        paths_to_check = [f'"{absolute_path}"']
        
        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")
        
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})
        
        # Debug print: Output the existing_entry after MongoDB query
        print(f"Debug: existing_entry after query = {existing_entry}")
        
        if existing_entry:
            # Delete the file from the filesystem
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
            
            # Remove the entry from the MongoDB collection
            result = collection.delete_one({'path': {'$in': paths_to_check}})
            
            if result.deleted_count:
                return "File and its database entry deleted successfully", 200
            else:
                return "Failed to delete file or its database entry", 400
        else:
            return "File path not found in the database", 404
    except Exception as e:
        return f"An error occurred: {str(e)}", 500



def download_id_get(id_):  # noqa: E501
    """
    Download a file
    :param id_: File path
    :type id_: str
    :rtype: None
    """
    try:
        # Check if the received path is an absolute path or relative to the current working directory
        if os.path.isabs(id_):
            file_path = id_
        else:
            file_path = os.path.join(os.getcwd(), id_)

        print(f"Debugging: Received path = {id_}")
        print(f"Debugging: Absolute path = {file_path}")
        print(f"Debugging: Current working directory = {os.getcwd()}")

        # Check if the file exists before attempting to send it
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True), 200
        else:
            return "File not found", 404

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Internal Server Error", 500



def query_post(query_file=None, python_file=None):  # noqa: E501 ###At the moment prints also new lines
    """Query (sql in .txt) and Manipulate (file.py) datalake items

     # noqa: E501

    :param query_file: 
    :type query_file: strstr
    :param python_file: 
    :type python_file: strstr

    :rtype: str
    """
    try:
        # Read the content directly from the FileStorage object and decode
        query_content = query_file.read().decode('utf-8') if query_file else ""
        python_content = python_file.read().decode('utf-8') if python_file else ""

        # Create the formatted string
        formatted_string = f'--query """{query_content}""" --script """{python_content}"""'
        os.system("whoami")

        return formatted_string, 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500



def replace_entry(path, file=None):  # noqa: E501###
    """Replace an existing entry and its associated file in S3 for the given path in MongoDB

     # noqa: E501

    :param path: 
    :type path: str
    :param metadata: 
    :type metadata: str
    :param file: 
    :type file: strstr

    :rtype: None
    """
        # Capture metadata and file from request
        ### WE CAN DECIDE WHETHER TO INCLUDE THIS AS FILE INSTEAD THAN JSON IN TEXT IN CURL
    metadata = request.form.get('metadata')

       # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['local']
    collection = db['metadata']

    # Specify the local folder for file storage
    local_folder = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_test_files\\COCO_dataset"

    try:
        # Check if the received path is an absolute path or relative to the current working directory
        if os.path.isabs(path):
            absolute_path = path
        else:
            absolute_path = os.path.join(os.getcwd(), path)
        # Debug print: Output the absolute_path
        print(f"Debug: absolute_path = {absolute_path}")
        
        # Create a JSON-like object for MongoDB query
        paths_to_check = [f'"{absolute_path}"']
        
        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")
        
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})

        # Debug: Print the result of the MongoDB query
        print(f"Debug: existing_entry = {existing_entry}")

        if not existing_entry:
            return "Entry not found for the given path", 404
        
        
        if metadata:
            metadata_obj = json.loads(metadata)
            print(metadata_obj)
            collection.find_one_and_replace({'path': {'$in': paths_to_check}}, metadata_obj)
        
        # Step 3: Replace file in local folder if file is provided
        if file:
            local_file_path = os.path.join(local_folder, os.path.basename(path))
            print(f"Debug: local_file_path = {local_file_path}")

            if not os.path.exists(local_file_path):
                return "Local file not found for the existing entry", 404

            with open(local_file_path, 'wb') as f:
                f.write(file.read())
        
        return "file at provided path replaced successfully. If metadata was included this replaced metadata associated with replaced file, ELSE the uploaded file is associated with pre-existing metadata", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500



def update_entry(path, body=None):  # noqa: E501
    """Update an existing entry in MongoDB based on the path and body."""

    print(f"Debug: Received body = {body}")

    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['local']
    collection = db['metadata']

    # Specify local folder for file storage
    local_folder = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_test_files\\COCO_dataset"

    try:
        # Determine absolute path
        absolute_path = os.path.join(local_folder, os.path.basename(path))
        
        print(f"Debug: Absolute path = {absolute_path}")

        # Create a JSON-like object for MongoDB query
        paths_to_check = [f'"{absolute_path}"']
        
        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")
        
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})
        
        print(f"Debug: Existing entry = {existing_entry}")

        if not existing_entry:
            return "Entry not found for the given path", 404

        # Update MongoDB entry if body is provided
        result = collection.find_one_and_update({'path': {'$in': paths_to_check}}, {'$set': body})

        if not result:
            return "Failed to update entry in MongoDB", 400

        return "Mongodb Entry  updated successfully", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500



def upload_post(file, json_data):
    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['local']
    collection = db['metadata']
    
    # Initialize transactional behavior flag
    success = False
    
    # Flag to check if a file replacement occurred
    file_replacement = False
    
    try:
        # Step 1: Save File --> THIS WILL THEN BE THE PATH/URL for S3
        file_path = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_test_files\\COCO_dataset"
        with open(os.path.join(file_path, file.filename), 'wb') as f:
            f.write(file.read())
        
        # Step 2: Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = json_data.read().decode('utf-8')
        json_data_list = json.loads(json_data_str)

        paths_to_check = [doc.get('path', '') for doc in json_data_list]
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})

        if existing_entry:
            for doc in json_data_list:
                if collection.find_one({'path': doc.get('path')}):
                    print(f"Path metadata already present in the collection --> Metadata is NOT update, File data is possibly replacing an existing file associate with path= {doc['path']}")
                    json_data_list.remove(doc)
                    file_replacement = True

        if json_data_list:
            collection.insert_many(json_data_list)

        # Step 3: Success message
        if file_replacement:
            return "Path metadata already present in MongoDB collection - File Upload Successful, Metadata is NOT updated", 201
        else:
            return "File Upload Successful, Metadata upload Successful ", 201

    except Exception as e:
        # Undo actions if one of them fails
        if os.path.exists(os.path.join(file_path, file.filename)):
            os.remove(os.path.join(file_path, file.filename))
        
        # This assumes that all inserted documents have a unique 'path'
        if 'json_data_list' in locals():
            paths_to_remove = [doc.get('path', '') for doc in json_data_list]
            collection.delete_many({'path': {'$in': paths_to_remove}})
        
        return f"Upload Failed: {str(e)}", 400



