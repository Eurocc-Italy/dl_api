# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class QueryAndProcessBody(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, query_file: str=None, python_file: str=None, config_json: str=None):  # noqa: E501
        """QueryAndProcessBody - a model defined in Swagger

        :param query_file: The query_file of this QueryAndProcessBody.  # noqa: E501
        :type query_file: str
        :param python_file: The python_file of this QueryAndProcessBody.  # noqa: E501
        :type python_file: str
        :param config_json: The config_json of this QueryAndProcessBody.  # noqa: E501
        :type config_json: str
        """
        self.swagger_types = {
            'query_file': str,
            'python_file': str,
            'config_json': str
        }

        self.attribute_map = {
            'query_file': 'query_file',
            'python_file': 'python_file',
            'config_json': 'config_json'
        }
        self._query_file = query_file
        self._python_file = python_file
        self._config_json = config_json

    @classmethod
    def from_dict(cls, dikt) -> 'QueryAndProcessBody':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The query_and_process_body of this QueryAndProcessBody.  # noqa: E501
        :rtype: QueryAndProcessBody
        """
        return util.deserialize_model(dikt, cls)

    @property
    def query_file(self) -> str:
        """Gets the query_file of this QueryAndProcessBody.


        :return: The query_file of this QueryAndProcessBody.
        :rtype: str
        """
        return self._query_file

    @query_file.setter
    def query_file(self, query_file: str):
        """Sets the query_file of this QueryAndProcessBody.


        :param query_file: The query_file of this QueryAndProcessBody.
        :type query_file: str
        """
        if query_file is None:
            raise ValueError("Invalid value for `query_file`, must not be `None`")  # noqa: E501

        self._query_file = query_file

    @property
    def python_file(self) -> str:
        """Gets the python_file of this QueryAndProcessBody.


        :return: The python_file of this QueryAndProcessBody.
        :rtype: str
        """
        return self._python_file

    @python_file.setter
    def python_file(self, python_file: str):
        """Sets the python_file of this QueryAndProcessBody.


        :param python_file: The python_file of this QueryAndProcessBody.
        :type python_file: str
        """

        self._python_file = python_file

    @property
    def config_json(self) -> str:
        """Gets the config_json of this QueryAndProcessBody.


        :return: The config_json of this QueryAndProcessBody.
        :rtype: str
        """
        return self._config_json

    @config_json.setter
    def config_json(self, config_json: str):
        """Sets the config_json of this QueryAndProcessBody.


        :param config_json: The config_json of this QueryAndProcessBody.
        :type config_json: str
        """

        self._config_json = config_json
