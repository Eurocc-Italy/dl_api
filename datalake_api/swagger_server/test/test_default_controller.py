# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from werkzeug.datastructures import FileStorage

from swagger_server.models.update_path_body import UpdatePathBody  # noqa: E501
from swagger_server.test import BaseTestCase
import urllib.parse
#import threading

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

    def assert200WithDetailsQUERYPROCESS(self, response, query_file, python_file):
        self.assert200(response, "Expected successful response for query and process")
        print("\n" + "=" * 80)
        print("SUCCESS: Query and Process Execution")
        print(f"Query File: {query_file.filename}")
        print(f"Python File: {python_file.filename}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.data.decode('utf-8')}")
        print("=" * 80 + "\n")

    def assert200WithReplaceDetails(self, response, path, metadata_file, file):
        self.assert200(response, "Expected successful response for replacement")
        print("\n" + "=" * 80)
        print(f"SUCCESS: Replacement for Path '{path}'")
        print(f"Metadata File: {metadata_file.filename}")
        print(f"File: {file.filename}")
        print(f"Response Status: {response.status_code}")
        response_json = json.loads(response.data.decode('utf-8'))
        print(f"Response Body: {json.dumps(response_json, indent=4)}")
        print("=" * 80 + "\n")
    
    
    ################################################################
    #DOWNLOAD

    def test_download_successful(self):
     """Test case for successfully downloading an item from the datalake."""
     existing_file_id = '/home/centos/dtaas_test_api/COCO_dataset/airplane_0585.jpg' 
     response = self.client.open(
          f'/v1/download?id=%2Fhome%2Fcentos%2Fdtaas_test_api%2FCOCO_dataset%2Fairplane_0585.jpg',
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

    def test_download_invalid_file_path(self):
        """Test case for downloading with an invalid file path."""
        invalid_file_id = 'invalid\\file\\path'
        response = self.client.open(
            f'/v1/download/{invalid_file_id}',
            method='GET'
            )
        self.assertEqual(response.status_code, 400, "Expected 400 for invalid file path")

# Test for downloading with an empty or missing file path
# Expectation: Should return a 400 Bad Request or a custom error response.
#def test_download_empty_file_path(self):
    # Test implementation...

# Test for path traversal attack vulnerability
# Expectation: Should prevent accessing unauthorized files and return a 400 or 403 response.
#def test_download_path_traversal_attack(self):
    # Test implementation...

# Test for handling URL-encoded file paths
# Expectation: Should decode the path correctly and download successfully if the file exists.
#def test_download_url_encoded_path(self):
    # Test implementation...

# Test for downloading files with special characters in the path
# Expectation: Should handle special characters correctly and download successfully if the file exists.
#def test_download_special_characters_in_path(self):
    # Test implementation...

# Test for downloading files from subdirectories
# Expectation: Should navigate subdirectories correctly and download successfully if the file exists.
#def test_download_file_from_subdirectories(self):
    # Test implementation...

# Test for downloading large files
# Expectation: Should handle large data transfers efficiently without timeout or memory issues.
#def test_download_large_file(self):
    # Test implementation...

# Test for handling multiple concurrent download requests
# Expectation: Should allow simultaneous downloads efficiently.
#def test_concurrent_downloads(self):
    # Test implementation...

# Test for downloading files with permission issues
# Expectation: Should respond with a 403 Forbidden or a custom error message if server lacks read permissions.
#def test_download_file_with_permission_issues(self):
    # Test implementation...




    ################################################################
    #DELETE
    def test_delete_succesful(self):
        """Test case for delete_file

        Delete a file in datalake (S3) and its MongoDB entry based on the given file_path
        """
        # !!! Remember the file path below must be registered in the MongoDB, else it won't be recognized !!!
        # The file path below is hardcoded in the test within the response 
        file_path = '/home/centos/dtaas_test_api/priceDetail.png'
        response = self.client.open(
            f'/v1/delete?file_path=%2Fhome%2Fcentos%2Fdtaas_test_api%2FpriceDetail.png',
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
     
    ###Other Delete Tests? 
    ### Database connectivity issue
    # This requires a mocking library like unittest.mock
    #from unittest.mock import patch
    #def test_delete_database_connectivity_issue(self):
    #    """Test case for a database connectivity issue during deletion."""
    #    with patch('path.to.database.connection.method', side_effect=Exception('Database Error')):
    #      response = self.client.open(
    #         f'/v1/delete?file_path={urllib.parse.quote("/path/to/testfile")}',
    #         method='DELETE'
    #     )
    #         self.assertEqual(response.status_code, 500, "Expected 500 for database connectivity issue")

    ### Concurrent deletion 
    # import threading
    # def test_delete_concurrent(self):
    # """Test case for concurrent deletion attempts."""
    # def delete_request():
    #    return self.client.open(
    #        f'/v1/delete?file_path={urllib.parse.quote("/path/to/testfile")}',
    #        method='DELETE'
    #    )
    #thread1 = threading.Thread(target=delete_request)
    #thread2 = threading.Thread(target=delete_request)
    #thread1.start()
    #thread2.start()
    #thread1.join()
    #thread2.join()

    # Additional assertions to check the outcome of concurrent requests



    ################################################################
    #Query_and_Process


    def test_query_post_successful_execution(self):
        """Test case for successful query and process execution."""
        query_file_content = "SELECT * FROM your_table;"
        python_file_content = "print('Hello, world!')"

        query_file = FileStorage(
            stream=BytesIO(query_file_content.encode()), 
            filename='query.txt'
        )
        python_file = FileStorage(
            stream=BytesIO(python_file_content.encode()), 
            filename='script.py'
        )

        data = {
            'query_file': query_file,
            'python_file': python_file
        }

        response = self.client.open(
            '/v1/query_and_process',
            method='POST',
            data=data,
            content_type='multipart/form-data'
        )
        self.assert200WithDetailsQUERYPROCESS(response, query_file, python_file)

    # Test for successful query and process execution
    #def test_query_post_successful_execution(self):
    #    # Setup and execute test for successful file processing
    #    # ...
#
    ## Test when the query file is missing
    #def test_query_post_missing_query_file(self):
    #    # Setup and execute test for missing query file scenario
    #    # ...
#
    ## Test when the Python file is missing (if applicable)
    #def test_query_post_missing_python_file(self):
    #    # Setup and execute test for missing Python file scenario
    #    # ...
#
    ## Test for invalid or corrupted file formats
    #def test_query_post_invalid_file_formats(self):
    #    # Setup and execute test for invalid file format scenario
    #    # ...
#
    ## Test error handling during file processing
    #def test_query_post_error_in_processing(self):
    #    # Setup and execute test for simulating an error in processing
    #    # ...
#
########IMPORTANT
######## AS OF NOW NO FILE HANDLING AND CLEAN UP

    ## Test file handling and cleanup after processing
    #def test_query_post_file_handling_and_cleanup(self):
    #    # Setup and execute test to check file handling and cleanup
    #    # ...
#
    #################################################################
    #REPLACE ENTRY
    def test_replace_entry_successful(self):
        """Test case for successful replacement of an entry and its file."""
        valid_path = '/home/centos/dtaas_test_api/COCO_dataset/airplane_0585.jpg'

                # Create file-like objects using FileStorage
        random_file_content= "hello"
        random_file = FileStorage(
            stream=BytesIO(random_file_content.encode()), 
            filename='script.py'
        )

        metadata_content = '{"path": "/home/centos/dtaas_test_api/COCO_dataset/airplane_0585.jpg"}'
        metadata_file = FileStorage(stream=BytesIO(metadata_content.encode()), filename='metadata.json')


        data = {
            'json_data': metadata_file,
            'file': random_file
        }

        response = self.client.open(
            f'/v1/replace?path=%2Fhome%2Fcentos%2Fdtaas_test_api%2FCOCO_dataset%2Fairplane_0585.jpg',
            method='PUT',
            data=data,
            content_type='multipart/form-data'
        )
        self.assert200WithReplaceDetails(response, valid_path, metadata_file, file)

    #################################################################
    #UPDATE ENTRY
    def test_update_entry(self):
        """Test case for update_entry

        Update an entry and optionally the file for the given path in MongoDB
        """
        body = UpdatePathBody()
        response = self.client.open(
            '/v1/update/{path}'.format(path='path_example'),
            method='PATCH',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_upload_post(self):
        """Test case for upload_post

        --Upload files to datalake (S3) and add entries to MongoDB-- OR --Replace Files in datalake(S3) and keep correspondig MongoDB entry-- Two options avoid creation of duplicate entries in MongoDB
        """
        data = dict(file='file_example',
                    json_data='json_data_example')
        response = self.client.open(
            '/v1/upload',
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
