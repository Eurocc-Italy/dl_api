import base64
import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from io import BytesIO
from pathlib import Path
from tempfile import mkdtemp

from decouple import Config, RepositoryEnv
from flask import send_file, request, Response, jsonify
from pymongo import MongoClient
from sh import pushd  # Import pushd from the sh library
from werkzeug.datastructures import FileStorage

import boto3
import botocore
import connexion
import six  # try to remove

from swagger_server.controllers.authorization_controller import decode_token
from swagger_server import util  # try to remove
from swagger_server.models.asset import Asset  # try to remove
from swagger_server.models.update_path_body import UpdatePathBody  # try to remove
from dlaas.tuilib.common import sanitize_dictionary


# Grab Main Directiories Paths
DOTENV_FILE = f"{os.getenv('HOME')}/.env"
env_config = Config(RepositoryEnv(DOTENV_FILE))


### START LOGGING CONFIGUARTION ###
class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.uuid = getattr(record, "uuid", "N/A")  # Default to 'N/A' if UUID is not present
        record.token = getattr(record, "token", "N/A")  # Default to 'N/A' if Token is not present
        record.user_id = getattr(record, "user_id", "N/A")  # Default to 'N/A' if user_id is not present
        return super().format(record)


# Set up for logging on file
LOG_DIR = env_config.get("LOG_DIR", "/var/log/datalake")
LOG_FILE = os.path.join(LOG_DIR, "api_datalake.log")

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging to log to both file and console
formatter = CustomFormatter(
    "%(asctime)s - %(levelname)s - UUID: %(uuid)s - Token: %(token)s - User ID: %(user_id)s - %(message)s"
)

# File handler for logging to file
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)

# Stream handler for logging to console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Set up the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
### END LOGGING CONFIGURATION ###


############################################
### Helper Functions


# Helper function for browse_files
def translate_sql_to_mongo(filter_param):
    """
    Translates a simplified SQL-like filter string to a MongoDB query.
    Supports basic operators '=', '>', '<', '!=', and logical operators 'AND', 'OR', 'NOT' in a case-insensitive manner.

    Args:
        filter_param (str): The filter string, e.g., "field1=value AND NOT field2>value OR field3!=value".

    Returns:
        dict: The MongoDB query.
    """
    # Operator mappings
    operators_mapping = {
        "=": "$eq",
        ">": "$gt",
        "<": "$lt",
        "!=": "$ne",
    }

    def parse_condition(condition):
        """
        Parses a single condition into a MongoDB query part, handling 'NOT' for simple negations.
        """
        is_negation = condition.strip().lower().startswith("not")
        if is_negation:
            condition = condition[4:]  # Remove 'NOT' prefix

        for op, mongo_op in operators_mapping.items():
            if op in condition:
                parts = condition.split(op)
                field, value = parts[0].strip(), parts[1].strip()
                # Apply negation if 'NOT' was detected
                if is_negation:
                    if mongo_op == "$eq":
                        return {field: {"$ne": value}}
                    else:
                        return {field: {"$not": {mongo_op: value}}}
                else:
                    return {field: {mongo_op: value}}
        return {}

    # Normalize logical operators to lowercase for consistent processing
    normalized_filter = filter_param.replace(" AND ", " and ").replace(" OR ", " or ").replace(" NOT ", " not ")

    query = {}

    # Process 'or' conditions
    if " or " in normalized_filter:
        or_parts = normalized_filter.split(" or ")
        query["$or"] = [parse_condition(part) for part in or_parts]
    # Process 'and' conditions
    elif " and " in normalized_filter:
        and_parts = normalized_filter.split(" and ")
        query["$and"] = [parse_condition(part) for part in and_parts]
    else:
        # Handle single condition without logical operators
        query = parse_condition(normalized_filter)

    return query


# Helper function modifying path to API
def sanitize_path(path):
    try:
        filename = os.path.basename(path)

        # 1. Check for prohibited characters and sequences
        if "/" in filename or "\0" in filename or "\\" in filename or ".." in filename or filename.startswith("."):
            raise ValueError("Filename contains prohibited characters or sequences")

        # 2. Remove potentially dangerous characters, including ;()` and **
        sanitized = re.sub(r'[*?"<>|$€#%!\'";\(\)`]+', "", filename)

        # 3. Ensure only allowed characters remain
        if not re.match(r"^[a-zA-Z0-9_\-.]+$", sanitized):
            raise ValueError("Filename contains disallowed characters")

        # 4. Final security check using normpath and basename
        normalized_path = os.path.normpath(sanitized)
        final_filename = os.path.basename(normalized_path)

        if final_filename != normalized_path:
            raise ValueError("Path contains directory traversal")

        return final_filename

    except Exception as e:
        raise ValueError(f"Invalid filename: {str(e)}")


# Helper function validating filename
def is_valid_filename(filename):
    try:
        sanitize_path(filename)
        return not os.path.isdir(filename)  # Additional check to ensure it's not a directory
    except ValueError:
        return False


# Helper content for query_post
# Define a blacklist of characters for config dltui
BLACKLIST = [";", "|", "&", "$", "<", ">", "`", "\\"]

# Fields that should bypass the blacklist check
BLACKLIST_EXCEPTIONS = ["s3_endpoint_url", "password"]

# Define regex patterns for each key of config dltui
REGEX_PATTERNS = {
    # "user": r"^[a-zA-Z0-9_\-]+$",
    # "password": r"^[a-zA-Z0-9_\-!@#\$%\^&\*\(\)]+$",
    # "ip": r"^\d{1,3}(\.\d{1,3}){3}$",
    # "port": r"^\d+$",
    # "database": r"^[a-zA-Z0-9_\-]+$",
    # "collection": r"^[a-zA-Z0-9_\-]+$",
    # "s3_endpoint_url": r"^https?://[a-zA-Z0-9_\-\.]+(:\d+)?(/.*)?$",
    # "s3_bucket": r"^[a-zA-Z0-9_\-]+$",
    # "pfs_prefix_path": r"^/[a-zA-Z0-9_\-/]+$",
    # "host": r"^[a-zA-Z0-9_\-\.]+$",
    # "venv_path": r"^/[a-zA-Z0-9_\-/]+$",
    # "ssh_key": r"^/[a-zA-Z0-9_\-/]+$",
    # "compute_partition": r"^[a-zA-Z0-9_\-]+$",
    # "upload_partition": r"^[a-zA-Z0-9_\-]+$",
    # "account": r"^[a-zA-Z0-9_\-]+$",
    # "qos": r"^[a-zA-Z0-9_\-]+$",
    # "mail": r"^[a-zA-Z0-9_\-\.@]+$",
    # "walltime": r"^\d{2}:\d{2}:\d{2}$",
    # "nodes": r"^\d+$",
    # "ntasks_per_node": r"^\d+$",
    "user": [r"[a-zA-Z0-9_]+"],  # any single word (word: character sequence containing alphanumerics or _)
    "password": [r"[a-zA-Z0-9_]+"],  # any single word
    "ip": [
        r"[a-zA-Z0-9_\.-]+[a-zA-Z0-9_-]+"
    ],  # any word sequence (with - and _) optionally delimited by dots, but not ending with one
    "port": [r"[0-9]+"],  # any number
    "database": [r"[a-zA-Z0-9_]+"],  # any single word
    "collection": [r"[a-zA-Z0-9_]+"],  # any single word
    "s3_endpoint_url": [r"(https?:\/\/)?([a-zA-Z0-9_-]+\.)+[a-zA-Z0-9_-]+\/?"],  # "https://XXX.(XXX.)*n.XXX/",
    "s3_bucket": [r"[a-zA-Z0-9_]+"],  # any single word
    "pfs_prefix_path": [r"\/([a-zA-Z0-9_-]+\/?)+"],  # any word sequence (no .) delimited by slashes, starting with /
    # config_server
    "user": [r"[a-zA-Z0-9_]+"],  # any single word (word: character sequence containing alphanumerics or _)
    "host": [
        r"[a-zA-Z0-9_\.-]+[a-zA-Z0-9_-]+"
    ],  # any word sequence (with - and _) optionally delimited by dots, but not ending with one
    "venv_path": [r"^(~)?\/([a-zA-Z0-9_.-]+\/?)+"],  # any word sequence delimited by slashes, can start with ~ or /
    "ssh_key": [r"^(~)?\/([a-zA-Z0-9_.-]+\/?)+"],  # any word sequence delimited by slashes, can start with ~ or /
    "compute_partition": [r"[a-zA-Z0-9_]+"],  # any single word,
    "upload_partition": [r"[a-zA-Z0-9_]+"],  # any single word
    "account": [r"[a-zA-Z0-9_]+"],  # any single word
    "qos": [r"[a-zA-Z0-9_]+"],  # any single word
    "mail": [r"[a-zA-Z0-9_\.]+@[a-zA-Z0-9_\.]+"],  # any valid email type (no dashes or pluses)
    "walltime": [r"([0-9]+-)?([0-9]+:)?([0-9]+:)?[0-9]+"],  # DD-HH:MM:SS
    "nodes": [r"[0-9]+(k|m)?"],  # any number, possibly ending with k or m
    "ntasks_per_node": [r"[0-9]+"],  # any number
}


# Helper function for query_post
def validate_config(config):
    for section, values in config.items():
        for key, value in values.items():
            # Skip blacklist check for specific keys
            if key not in BLACKLIST_EXCEPTIONS:
                # Check for blacklisted characters
                if any(char in value for char in BLACKLIST):
                    raise ValueError(f"Invalid character in {key}: {value}")

            # Validate using regex pattern
            if key in REGEX_PATTERNS:
                pattern = REGEX_PATTERNS[key]
                if not re.match(pattern, value):
                    raise ValueError(f"Invalid format for {key}: {value}")


########################################################################################################
########################################################################################################
### API ENDPOINT IMPLEMENTATIONS


def browse_files():
    """
    List files from the datalake with optional SQL-like filtering.

    Args:
        filter (str, optional): SQL-like filter to apply on the files list.

    Returns:
        Response: A JSON response containing the list of files or an error message.
    """
    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return jsonify({"message": "Unauthorized: Token missing or malformed\n"}), 401

    filter_param = request.args.get("filter", None)  # Extracting the SQL-like filter parameter

    logger.info(f"API call to browse_files with filter: {filter_param}", extra={"token": token, "user_id": user_id})

    try:
        mongo_query = translate_sql_to_mongo(filter_param) if filter_param is not None else {}

        # Initialize MongoDB client
        client = MongoClient(env_config.get("MONGO_HOST"), int(env_config.get("MONGO_PORT")))
        db = client[env_config.get("MONGO_DB_NAME")]
        collection = db[env_config.get("MONGO_COLLECTION_NAME")]

        if not mongo_query:  # This checks if the query is an empty dictionary
            files = collection.find({}, {"_id": 0, "s3_key": 1})  # Explicitly pass an empty dictionary
        else:
            files = collection.find(mongo_query, {"_id": 0, "s3_key": 1})

        file_list = [file["s3_key"] for file in files]

        return jsonify({"files": file_list}), 200

    except Exception as e:
        logger.error(f"An error occurred in browse_files: {str(e)}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


def delete_file(file_name, **kwargs):
    """
    Delete a file from the datalake (S3) and its corresponding entry in MongoDB.

    Args:
        file_name (str): The name of the file to be deleted.
        **kwargs: Additional keyword arguments (contains token information).

    Returns:
        tuple: A tuple containing the response message and status code.
    """
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed\n"}, 401

    sanitized_filename = sanitize_path(file_name)
    logger.info(
        "API call to %s", "delete_id_get", extra={"File": sanitized_filename, "token": token, "user_id": user_id}
    )

    # Initialize MongoDB client with decouple
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    try:
        #  validate the file path
        if not is_valid_filename(sanitized_filename):
            return "Invalid filename", 400

        existing_entry = collection.find_one({"s3_key": sanitized_filename})

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
                Key=sanitized_filename,
            )

            result = collection.delete_one({"s3_key": sanitized_filename})

            if result.deleted_count:
                return "File and its database entry deleted successfully", 200
            else:
                return "Failed to delete file or its database entry", 400
        else:
            return "File path not found in the database", 404
    except Exception as e:
        return f"An error occurred: {str(e)}\n", 500


def download_id_get(file_name, **kwargs):  # noqa: E501
    """
    Download a file from the datalake (S3).

    Args:
        file_name (str): The name of the file to be downloaded.
        **kwargs: Additional keyword arguments (contains token information).

    Returns:
        tuple: A tuple containing the file content and status code if successful, or an error message and status code if an error occurs.
    """
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed\n"}, 401

    # helper function to polish path to file
    sanitized_filename = sanitize_path(file_name)

    logger.info(
        "API call to %s", "download_id_get", extra={"File": sanitized_filename, "token": token, "user_id": user_id}
    )

    try:
        #  validate the file path
        if not is_valid_filename(sanitized_filename):
            return "Invalid filename", 400

        # NOTE: S3 credentials must be saved in ~/.aws/config file
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=env_config.get("S3_ENDPOINT_URL"),
        )

        s3_object = s3.get_object(Bucket=env_config.get("S3_BUCKET"), Key=sanitized_filename)

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


def query_post(query_file, python_file=None, **kwargs):
    """
    Query and manipulate datalake items using SQL queries and Python scripts.

    Args:
        query_file (FileStorage): The SQL query file.
        python_file (FileStorage, optional): The Python script file for data manipulation.
        **kwargs: Additional keyword arguments (contains token information).

    Returns:
        tuple: A tuple containing the response message and status code.
    """
    # Information printed for system log
    logger.debug("Dictionary with token info:")
    logger.debug(kwargs)

    try:
        config_json = json.loads(request.form["config_json"])
    except KeyError:
        config_json = None

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    unique_id = str(uuid.uuid4().hex)
    logger.info("API call to %s", "query_post", extra={"uuid": unique_id, "token": token, "user_id": user_id})

    try:
        # Ensure the query file and config JSON are provided
        if not query_file:
            return "Missing query file or configuration", 400

        if config_json:
            try:
                config_server = config_json["config_server"]
                sanitize_dictionary(config_server)
            except KeyError:
                config_server = None
            except ValueError as e:
                logger.error(f"Validation error: {str(e)}")
                return {"message": str(e)}, 400

            try:
                config_hpc = config_json["config_hpc"]
                sanitize_dictionary(config_server)
            except KeyError:
                config_hpc = None
            except ValueError as e:
                logger.error(f"Validation error: {str(e)}")
                return {"message": str(e)}, 400
        else:
            config_hpc = None
            config_server = None

        logger.debug(f"config_hpc: {config_hpc}")
        logger.debug(f"config_server: {config_server}")

        # Generate a unique ID and create a temporary directory
        unique_id = str(uuid.uuid4().hex)
        tdir = mkdtemp(prefix=unique_id, dir=os.getcwd())

        query_content = query_file.read().decode("utf-8")

        # Save script.py in the temporary directory if provided
        script_filename = f"user_script_{unique_id}.py"
        script_path = os.path.join(tdir, script_filename)
        if python_file:
            with open(script_path, "w") as script_out:
                script_out.write(python_file.read().decode("utf-8"))

        # Prepare and save launch.json in the temporary directory
        # NOTE : script_path should be a relative path to the temporary directory, otherwise on the "launcher"
        # it has a path like /home/centos/.../{uuid4.hex}/script.py which will not be found on HPC
        launch_data = {
            "sql_query": query_content,
            "script_path": os.path.basename(script_path) if python_file else None,
            "id": unique_id,
            "config_hpc": config_hpc or {},  # Insert empty dict if None
            "config_server": config_server or {},  # Insert empty dict if None
        }
        launch_path = os.path.join(tdir, "launch.json")
        with open(launch_path, "w") as launch_out:
            json.dump(launch_data, launch_out, indent=4)

        # Execute the command within the temporary directory
        # NOTE : same as before, since we're in the temporary directory we can just send the relative path of
        # the json file, otherwise the client version on HPC gets a wrong path
        with pushd(tdir):
            command = f"dl_tui_server launch.json"
            stdout, stderr = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).communicate()

        shutil.rmtree(tdir)  # Removing temporary directory. Comment for debugging.

        return f"Files processed successfully, ID: {unique_id}", 200

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}", 500


def replace_entry(file, json_data, **kwargs):
    """
    Replace an existing entry in MongoDB and its associated file in S3.

    Args:
        file (FileStorage): The file to be replaced.
        json_data (FileStorage): The JSON data containing metadata for the file.
        **kwargs: Additional keyword arguments (contains token information).

    Returns:
        tuple: A tuple containing the response message and status code.
    """

    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    # helper function to polish path to file
    sanitized_filename = sanitize_path(file.filename)

    logger.info(
        "API call to %s", "replace_entry", extra={"File": sanitized_filename, "token": token, "user_id": user_id}
    )

    # Initialize MongoDB client
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    if not collection.find_one({"s3_key": sanitized_filename}):
        return f"Replacement failed, file not found. Please use POST method to create a new entry", 400

    try:
        #  validate the file path
        if not is_valid_filename(sanitized_filename):
            return "Invalid filename", 400

        # NOTE: S3 credentials must be saved in ~/.aws/config file
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=env_config.get("S3_ENDPOINT_URL"),
        )

        # Insert json_data into MongoDB
        json_data_str = json_data.read().decode("utf-8")
        json_data_dict = json.loads(json_data_str)
        json_data_dict["s3_key"] = sanitized_filename
        json_data_dict["path"] = f"{env_config.get('PFS_PATH_PREFIX')}/{sanitized_filename}"

        s3.upload_fileobj(
            Fileobj=file,
            Bucket=env_config.get("S3_BUCKET"),
            Key=sanitized_filename,
        )
        collection.find_one_and_replace({"s3_key": sanitized_filename}, json_data_dict)

        return "File and Metadata replacement successful.", 201

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def update_entry(json_data, **kwargs):  # noqa: E501
    """
    Update an existing entry in MongoDB.

    Args:
        json_data (FileStorage): The JSON data containing updated metadata for the file.
        **kwargs: Additional keyword arguments (contains token information).

    Returns:
        tuple: A tuple containing the response message and status code.
    """

    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    logger.info("API call to %s", "update_entry", extra={"token": token, "user_id": user_id})

    # Verify that both 'file' (S3_key) and 'json_data' are passed correctly
    if "file" not in request.form or "json_data" not in request.files:
        return {"message": "Missing 'file' or 'json_data'"}, 400

    # Verify if implement sanification
    file = request.form["file"]

    # Initialize MongoDB client
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    try:
        if not collection.find_one({"s3_key": file}):
            return f"Update failed, file not found. Please use POST method to create a new entry", 400

        # Step 2: Insert json_data into MongoDB
        json_data_str = json_data.read().decode("utf-8")
        json_data_dict = json.loads(json_data_str)

        # modifying dictionary to use update operators, otherwise method will not work
        json_data_dict = {"$set": json_data_dict}

        collection.find_one_and_update({"s3_key": file}, json_data_dict)

        return "Metadata Updated Succesfully", 201

    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def upload_post(file, json_data, **kwargs):
    """
    Upload files to the datalake (S3) and add entries to MongoDB.

    Args:
        file (FileStorage): The file to be uploaded.
        json_data (FileStorage): The JSON data containing metadata for the file.
        **kwargs: Additional keyword arguments (contains token information).

    Returns:
        tuple: A tuple containing the response message and status code.
    """
    # Information printed for system log
    print("Dictionary with token info:")
    print(kwargs)

    # Extract the token from the Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Strip 'Bearer ' prefix to get the actual token
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub", "N/A")
    else:
        # Handle cases where the Authorization header is missing or improperly formatted
        return {"message": "Unauthorized: Token missing or malformed"}, 401

    # helper function to polish path to file
    sanitized_filename = sanitize_path(file.filename)

    logger.info("API call to %s", "upload_post", extra={"File": sanitized_filename, "token": token, "user_id": user_id})

    # Initialize MongoDB client
    mongo_host = env_config.get("MONGO_HOST", default="localhost")
    mongo_port = env_config.get("MONGO_PORT", default=27017, cast=int)
    mongo_db_name = env_config.get("MONGO_DB_NAME", default="datalake")
    mongo_collection_name = env_config.get("MONGO_COLLECTION_NAME", default="metadata")

    client = MongoClient(mongo_host, mongo_port)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    try:
        #  validate the file path
        if not is_valid_filename(sanitized_filename):
            return "Invalid filename", 400

        # NOTE: S3 credentials must be saved in ~/.aws/config file
        s3 = boto3.client(
            service_name="s3",
            endpoint_url=env_config.get("S3_ENDPOINT_URL"),
        )

        # Insert json_data into MongoDB
        # Properly read json_data and insert it into MongoDB
        json_data_str = json_data.read().decode("utf-8")
        json_data_dict = json.loads(json_data_str)
        json_data_dict["s3_key"] = sanitized_filename
        json_data_dict["path"] = f"{env_config.get('PFS_PATH_PREFIX')}/{sanitized_filename}"

        if collection.find_one({"s3_key": sanitized_filename}):
            return f"Upload Failed, entry is already present. Please use PUT method to update an existing entry", 400

        # Read file content into a binary stream
        s3.upload_fileobj(
            Fileobj=file,
            Bucket=env_config.get("S3_BUCKET"),
            Key=sanitized_filename,
        )
        collection.insert_one(json_data_dict)

        return "File and Metadata upload successful.", 201

    except boto3.exceptions.S3UploadFailedError as e:
        return (
            f"Upload Failed, entry likely already present. Please use the update_entry method. Error message: {str(e)}",
            400,
        )

    except Exception as e:
        # This assumes that all inserted documents have a unique 'path'
        if "json_data_dict" in locals():
            # paths_to_remove = [doc.get("s3_key", "") for doc in json_data_dict]
            collection.delete_one({"s3_key": sanitized_filename})

        return f"Upload Failed: {str(e)}", 400
