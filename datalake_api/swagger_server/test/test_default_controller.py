# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.update_path_body import UpdatePathBody  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_delete_file(self):
        """Test case for delete_file

        Delete a file in datalake (S3) and its MongoDB entry based on the given file_path
        """
        #Remember the file path below must be registered in the MongoDB, else it won't be recognized.
        file_path = '/home/centos/dtaas_test_api/priceDetail.png'
        response = self.client.open(
            f'/v1/delete?file_path=%2Fhome%2Fcentos%2Fdtaas_test_api%2FpriceDetail.png',
            method='DELETE'
        )
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_download_id_get(self):
        """Test case for download_id_get

        Download an item (using item path) from the datalake
        """
        response = self.client.open(
            '/v1/download/{id}'.format(id='id_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_query_post(self):
        """Test case for query_post

        Query (sql in .txt) and Manipulate (file.py) datalake items
        """
        data = dict(query_file='query_file_example',
                    python_file='python_file_example')
        response = self.client.open(
            '/v1/query_and_process',
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_replace_entry(self):
        """Test case for replace_entry

        Replace an existing entry and its associated file in S3 for the given path in MongoDB
        """
        data = dict(metadata='metadata_example',
                    file='file_example')
        response = self.client.open(
            '/v1/replace/{path}'.format(path='path_example'),
            method='PUT',
            data=data,
            content_type='multipart/form-data')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

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
