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
import uuid
import logging

import subprocess
from tempfile import mkdtemp
#from sh import pushd  # Import pushd from the sh library

#aider function to query_post
def escape_special_characters(content):
    # Escape double quotes
    content = content.replace('"', '\\"')
    # Escape asterisks
    content = content.replace('*', '\*')
    # Escape single quotes
    content = content.replace("'", "\'")
    # Escape parentheses
    content = content.replace('(', '\(')
    content = content.replace(')', '\)')
    # Escape new lines
    content = content.replace('\n', '\\n')
    # Escape carriage returns
    content = content.replace('\r', '\\r')
        # Escape single quotes
    content = content.replace("'", "\\'")

    return content

#aider function for path validation
def is_valid_file_path(path):
    """
    Validates the file path format.
    Implement the logic to check if the file path is valid.
    For example, you might want to check if it contains illegal characters, etc.
    """
    # Example check (you might need a more sophisticated validation based on your requirements)
    return not any(char in path for char in ['\\', ':', '*', '?', '"', '<', '>', '|'])




def download_id_get(id_):  # noqa: E501
    """
    Download a file
    :param id_: File path
    :type id_: str
    :rtype: None
    """
    try:
        # Validate the file path format
        if not is_valid_file_path(id_):
            return "Invalid file path format", 400
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
    

def delete_file(file_path):
    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['datalake']
    collection = db['metadata']
    
    try:

                # Validate the file path format
        if not is_valid_file_path(file_path):
            return "Invalid file path format", 400

        # Check if the received path is an absolute path or relative to the current working directory
        if os.path.isabs(file_path):
            absolute_path = file_path
        else:
            absolute_path = os.path.join(os.getcwd(), file_path)
        # Debug print: Output the absolute_path
        print(f"Debug: absolute_path = {absolute_path}")
        
        # Create a JSON-like object for MongoDB query
        paths_to_check = [f'{absolute_path}']
        
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

#INCLUDE A JSON PARAMETER, CONFIG FILE, WHERE IT HAS config_server = True/False and Config_client= True/False
def query_post(query_file=None, python_file=None, config_json=None):
    try:
        # Ensure the query file and config JSON are provided
        if not query_file:
            return "Missing query file or configuration", 400

        # Parse the configuration JSON
        config = json.loads(config_json.read().decode('utf-8'))
        config_server = config.get("config_server")  # Retrieve entire object or None
        config_client = config.get("config_client")  # Retrieve entire object or None

        # Generate a unique ID and create a temporary directory
        unique_id = str(uuid.uuid4())
        tdir = mkdtemp(prefix=unique_id, dir=os.getcwd())

        # Read and store sql_query.txt
        query_content = query_file.read().decode('utf-8')

        # Save script.py in the temporary directory if provided
        script_filename = f"user_script_{unique_id}.py"
        script_path = os.path.join(tdir, script_filename)
        if python_file:
            with open(script_path, 'w') as script_out:
                script_out.write(python_file.read().decode('utf-8'))

        # Prepare and save launch.json in the temporary directory
        launch_data = {
            "sql_query": query_content,
            "script_path": script_path,
            "ID": unique_id,
            "config_client": config_client or {},  # Insert empty dict if None
            "config_server": config_server or {}   # Insert empty dict if None
        }
        launch_path = os.path.join(tdir, 'launch.json')
        with open(launch_path, 'w') as launch_out:
            json.dump(launch_data, launch_out, indent=4)

        # Execute the command within the temporary directory
    #    with pushd(tdir):
    #        command = f"dtaas_tui_server {launch_path}"
    #        stdout, stderr = subprocess.Popen(
    #            command,
    #            shell=True,
    #            stdout=subprocess.PIPE,
    #            stderr=subprocess.PIPE,
    #        ).communicate()
        #shutil.rmtree(tdir)
        return f"Files processed successfully, ID: {unique_id}", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def replace_entry(path, file=None ,json_data=None):  # noqa: E501###
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

       # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['datalake']
    collection = db['metadata']

    # Specify the local folder for file storage
    local_folder = "/home/centos/dtaas_test_api/COCO_dataset"

    try:
        # Check if the received path is an absolute path or relative to the current working directory
        if os.path.isabs(path):
            absolute_path = path
        else:
            absolute_path = os.path.join(os.getcwd(), path)
        # Debug print: Output the absolute_path
        print(f"Debug: absolute_path = {absolute_path}")
        
        # Create a JSON-like object for MongoDB query
        paths_to_check = [f'{absolute_path}']
        
        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")
        
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})

        # Debug: Print the result of the MongoDB query
        print(f"Debug: existing_entry = {existing_entry}")

        if not existing_entry:
            return "Entry not found for the given path", 404
        
                # Step 2: Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = json_data.read().decode('utf-8')
        json_data_list = json.loads(json_data_str)

        paths_to_check = [doc.get('path', '') for doc in json_data_list]
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})


        if existing_entry:
            for doc in json_data_list:
                if collection.find_one_and_update({'path': doc.get('path')}, {'$set': doc} ):
                    print(f"Metadata updated,for path= {doc['path']}")
                    json_data_list.remove(doc)
        
        # Step 3: Replace file in local folder if file is provided
        if file:
            local_file_path = os.path.join(local_folder, os.path.basename(path))
            print(f"Debug: local_file_path = {local_file_path}")

            if not os.path.exists(local_file_path):
                return "Local file not found for the existing entry", 404

            with open(local_file_path, 'wb') as f:
                f.write(file.read())
        
        return "File updated succesfully, if metadata for file was included this has been updated", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500



def update_entry(path, file=None):  # noqa: E501
    """Update an existing entry in MongoDB based on the path and body."""

    print(f"Debug: Received body = {file}")

    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['datalake']
    collection = db['metadata']

    # Initialize the file_replacement flag
    file_replacement = False
    
    # Specify local folder for file storage
    local_folder = "/home/centos/dtaas_test_api/COCO_dataset"

    try:
        # Determine absolute path
        absolute_path = os.path.join(local_folder, os.path.basename(path))
        
        print(f"Debug: Absolute path = {absolute_path}")

        # Create a JSON-like object for MongoDB query
        paths_to_check = [f'{absolute_path}']
        
        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")
        
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})
        
        print(f"Debug: Existing entry = {existing_entry}")

        if not existing_entry:
            return "Entry not found for the given path", 404

        # Step 2: Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = file.read().decode('utf-8')
        json_data_list = json.loads(json_data_str)

        paths_to_check = [doc.get('path', '') for doc in json_data_list]
        existing_entry = collection.find_one({'path': {'$in': paths_to_check}})

        if existing_entry:
            for doc in json_data_list:
                if collection.find_one_and_update({'path': doc.get('path')}, {'$set': doc} ):
                    print(f"Metadata updated,for path= {doc['path']}")
                    json_data_list.remove(doc)
                    file_replacement = True

        # Step 3: Success message
        if file_replacement:
            return "Metadata is Updated Succesfully", 201
        else:
            return "Metadata not replaced ", 400

    except Exception as e:
        return f"An error occurred: {str(e)}", 500





def upload_post(file, json_data):
    # Initialize MongoDB client
    client = MongoClient('localhost', 27017)
    db = client['datalake']
    collection = db['metadata']
    
    # Initialize transactional behavior flag
    success = False
    
    # Flag to check if a file replacement occurred
    file_replacement = False
    
    try:
        # Step 1: Save File --> THIS WILL THEN BE THE PATH/URL for S3*****************************************
        file_path = "/home/centos/dtaas_test_api/COCO_dataset"
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



def get_config():
    #config_file_path = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_datalake_gitlab\\dtaas_test_api\\single_entry_metadata_test.json"
    #try:
    #    if os.path.exists(config_file_path):
    #        with open(config_file_path, 'r') as file:
    #            config_data = json.load(file)
    #        return config_data, 200
    #    else:
    #        return {"error": "Configuration not found"}, 404
    #except Exception as e:
    #    return {"error": str(e)}, 500
    return print("out of service for now")

def update_config():
    #config_file_path = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_datalake_gitlab\\dtaas_test_api\\single_entry_metadata_test.json"
    #try:
    #    # Extract new_config from the request
    #    if 'new_config' not in request.files:
    #        return {"error": "new_config file not provided"}, 400
    #    
    #    new_config_file = request.files['new_config']
    #    new_config = json.load(new_config_file)
#
    #    # Update the configuration
    #    with open(config_file_path, 'w') as file:
    #        json.dump(new_config, file, indent=4)
    #    return {"message": "Configuration updated successfully"}, 200
#
    #except json.JSONDecodeError as e:
    #    return {"error": f"Invalid JSON format: {str(e)}"}, 400
    #except Exception as e:
    #    return {"error": str(e)}, 500
    return print("out of service for now")