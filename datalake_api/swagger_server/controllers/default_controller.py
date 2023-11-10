import connexion
import six

from swagger_server import util


def delete_file(file_path):  # noqa: E501
    """Delete a file in datalake (S3) and its MongoDB entry based on the given file_path

     # noqa: E501

    :param file_path: 
    :type file_path: str

    :rtype: None
    """
    return 'do some magic!'


def download_id_get(id):  # noqa: E501
    """Download an item (using item path) from the datalake

     # noqa: E501

    :param id: 
    :type id: str

    :rtype: str
    """
    return 'do some magic!'


def query_post(query_file=None, python_file=None):  # noqa: E501
    """Query (sql in .txt) and Manipulate (file.py) datalake items

     # noqa: E501

    :param query_file: 
    :type query_file: strstr
    :param python_file: 
    :type python_file: strstr

    :rtype: str
    """
    return 'do some magic!'


def replace_entry(path, file=None, json_data=None):  # noqa: E501
    """Replace an existing entry and its associated file in S3 for the given path in MongoDB

     # noqa: E501

    :param path: 
    :type path: str
    :param file: 
    :type file: strstr
    :param json_data: 
    :type json_data: strstr

    :rtype: None
    """
    return 'do some magic!'


def update_entry(path, file=None):  # noqa: E501
    """Update metadata in MongoDB for a file given its path

     # noqa: E501

    :param path: 
    :type path: str
    :param file: 
    :type file: strstr

    :rtype: None
    """
    return 'do some magic!'


def upload_post(file=None, json_data=None):  # noqa: E501
    """--Upload files to datalake (S3) and add entries to MongoDB-- OR --Replace Files in datalake(S3) and keep correspondig MongoDB entry-- Two options avoid creation of duplicate entries in MongoDB

     # noqa: E501

    :param file: 
    :type file: strstr
    :param json_data: 
    :type json_data: strstr

    :rtype: str
    """
    return 'do some magic!'
