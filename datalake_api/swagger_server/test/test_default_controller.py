# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from werkzeug.datastructures import FileStorage
import os
from swagger_server.models.update_path_body import UpdatePathBody  # noqa: E501
from swagger_server.test import BaseTestCase
import urllib.parse
from decouple import config

class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""
    #The special assert for succefull execution are implemented for the most important tests.
    # Notice that by default Nothing prints if the test works

    def assert200WithDetailsDELETE(self, response, test_case_description):
        self.assert200(response, f"Response for {test_case_description}")
        print("\n" + "=" * 80)
        print(f"SUCCESS: {test_case_description}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.data.decode('utf-8')}")
        print("=" * 80 + "\n")
    
    def assert200WithDetailsDOWNLOAD(self, response, file_id):
        self.assert200(response, "Successful download response")
        print("\n" + "=" * 80)
        print(f"SUCCESS: Downloaded file with ID '{file_id}'")
        print(f"Response Status: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
        print(f"Response Size: {len(response.data)} bytes")
        print("=" * 80 + "\n")

    def assert200WithDetailsQUERYPROCESS(self, response, query_file, python_file, config_json):
        self.assert200(response, "Expected successful response for query and process")
        print("\n" + "=" * 80)
        print("SUCCESS: Query and Process Execution")
        print(f"Query File: {query_file.filename}")
        print(f"Python File: {python_file.filename}")
        print(f"Config File: {config_json.filename}")  # Add this line to print the config file name
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.data.decode('utf-8')}")
        print("=" * 80 + "\n")

    def assert200WithDetailsREPLACE(self, response, path, metadata_file, file):
        self.assert200(response, "Expected successful response for replacement")
        print("\n" + "=" * 80)
        print(f"SUCCESS: Replacement for Path '{path}'")
        print(f"Metadata File: {metadata_file.filename}")
        print(f"File: {file.filename}")
        print(f"Response Status: {response.status_code}")
        response_json = json.loads(response.data.decode('utf-8'))
        print(f"Response Body: {json.dumps(response_json, indent=4)}")
        print("=" * 80 + "\n")
    
    def assert200WithDetailsUPDATE(self, response, path, metadata_file):
        """Custom assert method for detailed test responses."""
        try:
            self.assertEqual(response.status_code, 201, "Expected status code 200")
            print("\n" + "=" * 80)
            print(f"SUCCESS: Update entry for path {path}")
            print(f"Metadata File: {metadata_file.filename}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.data.decode('utf-8')}")
            print("=" * 80 + "\n")
        except AssertionError as e:
            print("\n" + "=" * 80)
            print("FAILED: Update entry test")
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.data.decode('utf-8')}")
            print("=" * 80 + "\n")
            raise e
 
    def assert200WithDetailsUPLOAD(self, response, file, metadata_file):
        """Custom assert method for detailed test responses."""
        try:
            self.assertEqual(response.status_code, 201, "Expected status code 201")
            print("\n" + "=" * 80)
            print("SUCCESS: File and Metadata Upload")
            print(f"File Name: {file.filename}")
            print(f"Metadata File: {metadata_file.filename}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.data.decode('utf-8')}")
            print("=" * 80 + "\n")
        except AssertionError as e:
            print("\n" + "=" * 80)
            print("FAILED: Upload Test")
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.data.decode('utf-8')}")
            print("=" * 80 + "\n")
            raise e
    ################################################################
    #DOWNLOAD

    def test_download_successful(self):
        """Test case for successfully downloading an item from the datalake."""
        local_folder = config('TEST_LOCAL_FOLDER', default='/home/centos/dtaas_test_api/COCO_dataset')
        file_name = config('TEST_IMAGE_1', default='airplane_0585.jpg')
        existing_file_id = f'{local_folder}/{file_name}'
        encoded_file_id = urllib.parse.quote(existing_file_id)

        response = self.client.open(
            f'/v1/download?id={encoded_file_id}',
            method='GET'
        )
        self.assert200WithDetailsDOWNLOAD(response, existing_file_id)



    def test_download_file_not_found(self):
        """Test case for attempting to download a file that doesn't exist."""
        nonexistent_file_id = 'path/to/nonexistent/file'
        response = self.client.open(
            f'/v1/download/{nonexistent_file_id}',
            method='GET'
            )
        self.assertEqual(response.status_code, 404, "Expected 404 for nonexistent file")



    ################################################################
    #DELETE
    def test_delete_succesful(self):
        """Test case for delete_file"""
        local_folder = config('TEST_LOCAL_FOLDER', default='/home/centos/dtaas_test_api/COCO_dataset')
        file_name = config('TEST_IMAGE_2', default='priceDetail.png')
        file_path = f'{local_folder}/{file_name}'
        encoded_file_path = urllib.parse.quote(file_path)

        response = self.client.open(
            f'/v1/delete?file_path={encoded_file_path}',
            method='DELETE'
        )
        self.assert200WithDetailsDELETE(response, f"Delete file at {file_path}")


    def test_delete_nonexistent_file(self):
        """Test case for attempting to delete a nonexistent file."""
        response = self.client.open(
            f'/v1/delete?file_path={urllib.parse.quote("/path/to/nonexistentfile")}',
            method='DELETE'
        )
        self.assertEqual(response.status_code, 404, "Expected 404 for nonexistent file")
    
    def test_delete_invalid_file_path(self):
        """Test case for deleting a file with an invalid file path."""
        print("Running test_delete_invalid_file")
        invalid_file_path = 'invalid/file\\path'
        response = self.client.open(
            f'/v1/delete?file_path={urllib.parse.quote(invalid_file_path)}',
           method='DELETE'
    )
        self.assertEqual(response.status_code, 400, "Expected 400 for invalid file path")   



    ################################################################
    #Query_and_Process
    def test_query_post_successful_execution(self):
        """Test case for successful query and process execution."""
        query_file_content = config('TEST_QUERY_FILE_CONTENT', default="SELECT * FROM your_table;")
        python_file_content = config('TEST_PYTHON_FILE_CONTENT', default="print('Hello, world!')")
        config_json_content = config('TEST_CONFIG_JSON_CONTENT', default=json.dumps({
            "config_server": {"user": "hpc_user", "host": "hpc.example.com", "venv_path": "/path/to/venv", "ssh_key": "/path/to/ssh_key", "partition": "compute", "account": "hpc_account", "mail": "user@example.com", "walltime": "2:00:00", "nodes": 2, "ntasks_per_node": 4},
            "config_client": {"user": "db_user", "password": "db_password", "ip": "192.168.1.1", "port": "27017", "database": "metadata_db", "collection": "metadata_collection"}
        }))

        query_file = FileStorage(
            stream=BytesIO(query_file_content.encode()), 
            filename='query.txt'
        )
        python_file = FileStorage(
            stream=BytesIO(python_file_content.encode()), 
            filename='script.py'
        )
        config_json = FileStorage(
            stream=BytesIO(config_json_content.encode()),
            filename='config.json'
        )

        data = {
            'query_file': query_file,
            'python_file': python_file,
            'config_json': config_json
        }

        response = self.client.open(
            '/v1/query_and_process',
            method='POST',
            data=data,
            content_type='multipart/form-data'
        )
        self.assert200WithDetailsQUERYPROCESS(response, query_file, python_file, config_json)

    #################################################################
    #REPLACE ENTRY
    def test_replace_entry_successful(self):
        """Test case for successful replacement of an entry and its file."""
        local_folder = config('TEST_LOCAL_FOLDER', default='/home/centos/dtaas_test_api/COCO_dataset')
        file_name = config('TEST_IMAGE_1', default='airplane_0585.jpg')
        valid_path = f'{local_folder}/{file_name}'

        # Reading the file as a generic binary string
        with open(valid_path, 'rb') as file_obj:
            file_content = file_obj.read()

        file = FileStorage(
            stream=BytesIO(file_content),
            filename=os.path.basename(valid_path),
            content_type='application/octet-stream'  # General binary content type
        )

        # Reading the JSON metadata from the environment variable
        metadata_content = config('TEST_METADATA_CONTENT', default=json.dumps([{"id": 1, "path": "/home/centos/dtaas_test_api/COCO_dataset/airplane_0585.jpg" }]))

        metadata_file = FileStorage(
            stream=BytesIO(metadata_content.encode()),
            filename='metadata.json',
            content_type='application/json'
        )

        data = {
            'file': file,
            'json_data': metadata_file
        }


        response = self.client.open(
            f'/v1/replace?path={urllib.parse.quote(valid_path)}',
            method='PUT',
            data=data,
            content_type='multipart/form-data'
        )

        # Debugging output for failure
        if response.status_code != 200:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response body: {response.data.decode('utf-8')}")

        self.assert200WithDetailsREPLACE(response, valid_path, metadata_file, file)




    #################################################################
    #UPDATE ENTRY
    def test_update_entry(self):
        """Test case for update_entry - Update an entry in MongoDB."""
        local_folder = config('TEST_LOCAL_FOLDER', default='/home/centos/dtaas_test_api/COCO_dataset')
        file_name = config('TEST_IMAGE_1', default='airplane_0585.jpg')
        valid_path = f'{local_folder}/{file_name}'

        # Reading the JSON metadata from the environment variable
        #Notice that the path in the TEST_METADATA_CONTENT must match path valid_path above
        metadata_content = config('TEST_METADATA_CONTENT', default=json.dumps([{"id": 100, "path": "/home/centos/dtaas_test_api/airplane_0585.jpg" }]))

        metadata_file = FileStorage(
            stream=BytesIO(metadata_content.encode()),
            filename='metadata.json',
            content_type='application/json'
        )

        # Confirm the file object before sending
        if not metadata_file or not hasattr(metadata_file, 'read'):
            print("Error: metadata_file is not a valid FileStorage object.")
            return

        data = {
            'file': metadata_file
        }

        response = self.client.open(
            f'/v1/update?path={urllib.parse.quote(valid_path)}',
            method='PATCH',
            data=data,
            content_type='multipart/form-data'
        )

        self.assert200WithDetailsUPDATE(response, valid_path, metadata_file)




    #################################################################
    #UPLOAD 
    def test_upload_post(self):
        """Test case for upload_post - Upload files to datalake and add entries to MongoDB."""
        local_folder = config('TEST_LOCAL_FOLDER', default='/home/centos/dtaas_test_api/COCO_dataset')
        file_name = config('TEST_IMAGE_1', default='airplane_0585.jpg')
        image_path = f'{local_folder}/{file_name}'
    
        with open(image_path, 'rb') as img_file:
            image_content = img_file.read()
    
        file = FileStorage(
            stream=BytesIO(image_content),
            filename=os.path.basename(image_path),
            content_type='application/octet-stream'
        )
    
        # Reading the JSON metadata from the environment variable
        metadata_content = config('TEST_METADATA_CONTENT', default=json.dumps([{"id": 100, "path": "/home/centos/dtaas_test_api/airplane_0585.jpg" }]))
    
        metadata_file = FileStorage(
            stream=BytesIO(metadata_content.encode()),
            filename='metadata.json',
            content_type='application/json'
        )
    
        data = {
            'file': file,
            'json_data': metadata_file
        }
    
        response = self.client.open(
            '/v1/upload',
            method='POST',
            data=data,
            content_type='multipart/form-data'
        )
        self.assert200WithDetailsUPLOAD(response, file, metadata_file)

if __name__ == '__main__':
    import unittest
    unittest.main()

