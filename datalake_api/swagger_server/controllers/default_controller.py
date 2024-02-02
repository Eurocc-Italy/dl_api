import connexion
import six
from io import BytesIO

from swagger_server.models.asset import Asset  # noqa: E501
from swagger_server import util
from werkzeug.datastructures import FileStorage

import os
import shutil
from flask import send_file, request, Response
import json
from pymongo import MongoClient

import base64
import connexion
import six

from swagger_server.models.update_path_body import UpdatePathBody  # noqa: E501
from swagger_server import util
import uuid
import logging

from decouple import Config, RepositoryEnv
import subprocess
from tempfile import mkdtemp
from sh import pushd  # Import pushd from the sh library

import boto3, botocore

DOTENV_FILE = f"{os.getenv('HOME')}/.env"
env_config = Config(RepositoryEnv(DOTENV_FILE))
print(env_config)


class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.uuid = getattr(record, "uuid", "N/A")  # Default to 'N/A' if UUID is not present
        record.token = getattr(record, "token", "N/A")  # Default to 'N/A' if Token is not present
        return super().format(record)


# Configure logging with the custom formatter
formatter = CustomFormatter("%(asctime)s - %(levelname)s - UUID: %(uuid)s - Token: %(token)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


# aider function to query_post
def escape_special_characters(content):
    # Escape double quotes
    content = content.replace('"', '\\"')
    # Escape asterisks
    content = content.replace("*", "\*")
    # Escape single quotes
    content = content.replace("'", "'")
    # Escape parentheses
    content = content.replace("(", "\(")
    content = content.replace(")", "\)")
    # Escape new lines
    content = content.replace("\n", "\\n")
    # Escape carriage returns
    content = content.replace("\r", "\\r")
    # Escape single quotes
    content = content.replace("'", "\\'")

    return content


# aider function for path validation
def is_valid_file_path(path):
    """
    Validates the file path format.
    Implement the logic to check if the file path is valid.
    For example, you might want to check if it contains illegal characters, etc.
    """
    # Example check (you might need a more sophisticated validation based on your requirements)
    return not any(char in path for char in ["\\", ":", "*", "?", '"', "<", ">", "|"])


def download_id_get(file_name, **kwargs):  # noqa: E501
    """
    Download a file
    :param file_name: File name
    :type id_: str
    :rtype: None
    """
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed\n"}, 401

    logger.info("API call to %s", "download_id_get", extra={"File": file_name, "token": token})

    try:
        # NOTE: S3 credentials must be saved in ~/.aws/config file
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=env_config.get("S3_ENDPOINT_URL"),
        )

        ## NOTE: if TUI requires Downlaod in VM, It might be necessary to uncomment below
        # s3.download_file(
        #    Bucket=env_config.get("S3_BUCKET"),
        #    Filename=f"/home/centos/DOWNLOAD/{file_name}",
        #    Key=file_name,
        # )
        # return f"Download successful. File is available at: /home/centos/DOWNLOAD/{file_name}\n", 200

        # Get object from bucket
        s3_object = s3.get_object(Bucket=env_config.get("S3_BUCKET"), Key=file_name)

        # Stream the file directly from S3 to the client
        # def generate():
        #    for chunk in s3_object["Body"].iter_chunks(chunk_size=4096):
        #        yield chunk
        # return Response(generate(), content_type=s3_object["ContentType"])

        # return send_file(f"/home/centos/DOWNLOAD/{file_name}", as_attachment=True), 200

        # Read the entire file content
        file_content = s3_object["Body"].read()

        return Response(file_content, content_type=s3_object["ContentType"])

    except botocore.exceptions.ClientError as e:
        # Handle specific S3 client errors (e.g., file not found)
        if e.response["Error"]["Code"] == "NoSuchKey":
            return "File not found\n", 404
        else:
            return "S3 Client Error\n", 500

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Internal Server Error\n", 500


def delete_file(file_name, **kwargs):
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed\n"}, 401

    logger.info("API call to %s", "delete_id_get", extra={"File": file_name, "token": token})

    # Initialize MongoDB client with decouple
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    try:
        existing_entry = collection.find_one({"s3_key": file_name})

        # Debug print: Output the existing_entry after MongoDB query
        print(f"Debug: existing_entry after query = {existing_entry}")

        if existing_entry:
            # NOTE: S3 credentials must be saved in ~/.aws/config file
            s3 = boto3.client(
                service_name="s3",
                endpoint_url=env_config.get("S3_ENDPOINT_URL"),
            )

            s3.delete_object(
                Bucket=env_config.get("S3_BUCKET"),
                Key=file_name,
            )

            result = collection.delete_one({"s3_key": file_name})

            if result.deleted_count:
                return "File and its database entry deleted successfully", 200
            else:
                return "Failed to delete file or its database entry", 400
        else:
            return "File path not found in the database", 404
    except Exception as e:
        return f"An error occurred: {str(e)}\n", 500


def query_post(query_file, python_file=None, config_json=None, **kwargs):
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    unique_id = str(uuid.uuid4().hex)
    logger.info("API call to %s", "query_post", extra={"uuid": unique_id, "token": token})

    try:
        # Ensure the query file and config JSON are provided
        if not query_file:
            return "Missing query file or configuration", 400

        if config_json:
            # Parse the configuration JSON
            config = json.loads(config_json.read().decode("utf-8"))
            config_server = config.get("config_server")  # Retrieve entire object or None
            config_client = config.get("config_client")  # Retrieve entire object or None
        else:
            config_client = None
            config_server = None

        # Generate a unique ID and create a temporary directory
        unique_id = str(uuid.uuid4().hex)
        tdir = mkdtemp(prefix=unique_id, dir=os.getcwd())

        # Read and store sql_query.txt
        query_content = query_file.read().decode("utf-8")

        # Save script.py in the temporary directory if provided
        script_filename = f"user_script_{unique_id}.py"
        script_path = os.path.join(tdir, script_filename)
        if python_file:
            with open(script_path, "w") as script_out:
                script_out.write(python_file.read().decode("utf-8"))

        # Prepare and save launch.json in the temporary directory
        # NOTE (Luca): script_path should be a relative path to the temporary directory, otherwise on the "launcher"
        # it has a path like /home/centos/.../{uuid4.hex}/script.py which will not be found on HPC
        launch_data = {
            "sql_query": query_content,
            "script_path": os.path.basename(script_path),
            "id": unique_id,
            "config_client": config_client or {},  # Insert empty dict if None
            "config_server": config_server or {},  # Insert empty dict if None
        }
        launch_path = os.path.join(tdir, "launch.json")
        with open(launch_path, "w") as launch_out:
            json.dump(launch_data, launch_out, indent=4)

        # Execute the command within the temporary directory
        # NOTE (Luca): same as before, since we're in the temporary directory we can just send the relative path of
        # the json file, otherwise the client version on HPC gets a wrong path
        with pushd(tdir):
            command = f"dtaas_tui_server launch.json"
            stdout, stderr = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).communicate()
        # shutil.rmtree(tdir)
        return f"Files processed successfully, ID: {unique_id}", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def replace_entry(path, file=None, json_data=None, **kwargs):  # noqa: E501###
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    unique_id = str(uuid.uuid4().hex)
    logger.info("API call to %s", "replace_entry", extra={"uuid": unique_id, "token": token})

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
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    # Specify the local folder for file storage
    local_folder = env_config.get("LOCAL_FOLDER", default="/home/centos/dtaas_test_api/COCO_dataset")

    try:
        # Check if the received path is an absolute path or relative to the current working directory
        if os.path.isabs(path):
            absolute_path = path
        else:
            absolute_path = os.path.join(os.getcwd(), path)
        # Debug print: Output the absolute_path
        print(f"Debug: absolute_path = {absolute_path}")

        # Create a JSON-like object for MongoDB query
        paths_to_check = [f"{absolute_path}"]

        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")

        existing_entry = collection.find_one({"path": {"$in": paths_to_check}})

        # Debug: Print the result of the MongoDB query
        print(f"Debug: existing_entry = {existing_entry}")

        if not existing_entry:
            return "Entry not found for the given path", 404

            # Step 2: Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = json_data.read().decode("utf-8")
        json_data_dict = json.loads(json_data_str)

        paths_to_check = [doc.get("path", "") for doc in json_data_dict]
        existing_entry = collection.find_one({"path": {"$in": paths_to_check}})

        if existing_entry:
            for doc in json_data_dict:
                if collection.find_one_and_update({"path": doc.get("path")}, {"$set": doc}):
                    print(f"Metadata updated,for path= {doc['path']}")
                    json_data_dict.remove(doc)

        # Step 3: Replace file in local folder if file is provided
        if file:
            local_file_path = os.path.join(local_folder, os.path.basename(path))
            print(f"Debug: local_file_path = {local_file_path}")

            if not os.path.exists(local_file_path):
                return "Local file not found for the existing entry", 404

            with open(local_file_path, "wb") as f:
                f.write(file.read())

        return "File updated succesfully, if metadata for file was included this has been updated", 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def update_entry(path, file=None, **kwargs):  # noqa: E501
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    unique_id = str(uuid.uuid4().hex)
    logger.info("API call to %s", "update_entry", extra={"uuid": unique_id, "token": token})

    """Update an existing entry in MongoDB based on the path and body."""

    print(f"Debug: Received body = {file}")

    # Initialize MongoDB client
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    # Initialize the file_replacement flag
    file_replacement = False

    # Specify local folder for file storage
    local_folder = env_config.get("LOCAL_FOLDER", default="/home/centos/dtaas_test_api/COCO_dataset")

    try:
        # Determine absolute path
        absolute_path = os.path.join(local_folder, os.path.basename(path))

        print(f"Debug: Absolute path = {absolute_path}")

        # Create a JSON-like object for MongoDB query
        paths_to_check = [f"{absolute_path}"]

        # Debug print: Output the paths_to_check before MongoDB query
        print(f"Debug: paths_to_check before query = {paths_to_check}")

        existing_entry = collection.find_one({"path": {"$in": paths_to_check}})

        print(f"Debug: Existing entry = {existing_entry}")

        if not existing_entry:
            return "Entry not found for the given path", 404

        # Step 2: Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = file.read().decode("utf-8")
        json_data_dict = json.loads(json_data_str)

        paths_to_check = [doc.get("path", "") for doc in json_data_dict]
        existing_entry = collection.find_one({"path": {"$in": paths_to_check}})

        if existing_entry:
            for doc in json_data_dict:
                if collection.find_one_and_update({"path": doc.get("path")}, {"$set": doc}):
                    print(f"Metadata updated,for path= {doc['path']}")
                    json_data_dict.remove(doc)
                    file_replacement = True

        # Step 3: Success message
        if file_replacement:
            return "Metadata is Updated Succesfully", 201
        else:
            return "Metadata not replaced", 400

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def upload_post(file, json_data, **kwargs):
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    logger.info("API call to %s", "upload_post", extra={"File": file.filename, "token": token})

    # Initialize MongoDB client
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    try:
        # NOTE: S3 credentials must be saved in ~/.aws/config file
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=env_config.get("S3_ENDPOINT_URL"),
        )

        # Step 2: Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = json_data.read().decode("utf-8")
        json_data_dict = json.loads(json_data_str)
        json_data_dict["s3_key"] = file.filename
        json_data_dict["path"] = f"{env_config.get('PFS_PATH_PREFIX')}{env_config.get('S3_BUCKET')}/{file.filename}"

        if collection.find_one({"s3_key": file.filename}):
            return f"Upload Failed, entry is already present. Please use PUT method to update an existing entry", 400

        # Read file content into a binary stream

        # NOTE: upload_file was changes to upload_fileobject
        # if file is necessary to TUI it might be useful to recover also upload_file
        s3.upload_fileobj(
            Fileobj=file,
            Bucket=env_config.get("S3_BUCKET"),
            Key=file.filename,
        )
        collection.insert_one(json_data_dict)

        # Step 3: Success message
        return "File and Metadata upload successful.", 201

    except boto3.exceptions.S3UploadFailedError as e:
        return (
            f"Upload Failed, entry likely already present. Please use the update_entry method. Error message: {str(e)}",
            400,
        )

    except Exception as e:
        # Undo actions if one of them fails
        # if os.path.exists(os.path.join(file_path, file.filename)):
        #     os.remove(os.path.join(file_path, file.filename))

        # This assumes that all inserted documents have a unique 'path'
        if "json_data_dict" in locals():
            # paths_to_remove = [doc.get("s3_key", "") for doc in json_data_dict]
            collection.delete_one({"s3_key": file.filename})

        return f"Upload Failed: {str(e)}", 400


def get_config(**kwargs):
    # Information printed for system log
    # print("Dictionary with token info:")
    # print(kwargs)

    # Extract the token from the Authorization header
    # auth_header = request.headers.get('Authorization')
    #
    # if auth_header and auth_header.startswith('Bearer '):
    #    token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    # else:
    #    # Handle cases where the Authorization header is missing or improperly formatted
    #    return {"message": "Unauthorized: Token missing or malformed"}, 401
    #
    # unique_id = str(uuid.uuid4().hex)
    # logger.info('API call to %s', 'get_config', extra={'uuid': unique_id, 'token': token})

    # config_file_path = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_datalake_gitlab\\dtaas_test_api\\single_entry_metadata_test.json"
    # try:
    #    if os.path.exists(config_file_path):
    #        with open(config_file_path, 'r') as file:
    #            config_data = json.load(file)
    #        return config_data, 200
    #    else:
    #        return {"error": "Configuration not found"}, 404
    # except Exception as e:
    #    return {"error": str(e)}, 500
    return print("out of service for now")


def update_config(**kwargs):
    # Information printed for system log
    # print("Dictionary with token info:")
    # print(kwargs)

    # Extract the token from the Authorization header
    # auth_header = request.headers.get('Authorization')
    #
    # if auth_header and auth_header.startswith('Bearer '):
    #    token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
    # else:
    #    # Handle cases where the Authorization header is missing or improperly formatted
    #    return {"message": "Unauthorized: Token missing or malformed"}, 401
    #
    # unique_id = str(uuid.uuid4().hex)
    # logger.info('API call to %s', 'update_config', extra={'uuid': unique_id, 'token': token})

    # config_file_path = "C:\\Users\\IvanGentile\\OneDrive - Net Service S.p.A\\Desktop\\API_datalake_gitlab\\dtaas_test_api\\single_entry_metadata_test.json"
    # try:
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
    # except json.JSONDecodeError as e:
    #    return {"error": f"Invalid JSON format: {str(e)}"}, 400
    # except Exception as e:
    #    return {"error": str(e)}, 500
    return print("out of service for now")
