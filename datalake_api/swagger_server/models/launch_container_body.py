# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class LaunchContainerBody(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, query_file: str=None, container_file: str=None, exec_command: str=None):  # noqa: E501
        """LaunchContainerBody - a model defined in Swagger

        :param query_file: The query_file of this LaunchContainerBody.  # noqa: E501
        :type query_file: str
        :param container_file: The container_file of this LaunchContainerBody.  # noqa: E501
        :type container_file: str
        :param exec_command: The exec_command of this LaunchContainerBody.  # noqa: E501
        :type exec_command: str
        """
        self.swagger_types = {
            'query_file': str,
            'container_file': str,
            'exec_command': str
        }

        self.attribute_map = {
            'query_file': 'query_file',
            'container_file': 'container_file',
            'exec_command': 'exec_command'
        }
        self._query_file = query_file
        self._container_file = container_file
        self._exec_command = exec_command

    @classmethod
    def from_dict(cls, dikt) -> 'LaunchContainerBody':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The launch_container_body of this LaunchContainerBody.  # noqa: E501
        :rtype: LaunchContainerBody
        """
        return util.deserialize_model(dikt, cls)

    @property
    def query_file(self) -> str:
        """Gets the query_file of this LaunchContainerBody.


        :return: The query_file of this LaunchContainerBody.
        :rtype: str
        """
        return self._query_file

    @query_file.setter
    def query_file(self, query_file: str):
        """Sets the query_file of this LaunchContainerBody.


        :param query_file: The query_file of this LaunchContainerBody.
        :type query_file: str
        """
        if query_file is None:
            raise ValueError("Invalid value for `query_file`, must not be `None`")  # noqa: E501

        self._query_file = query_file

    @property
    def container_file(self) -> str:
        """Gets the container_file of this LaunchContainerBody.


        :return: The container_file of this LaunchContainerBody.
        :rtype: str
        """
        return self._container_file

    @container_file.setter
    def container_file(self, container_file: str):
        """Sets the container_file of this LaunchContainerBody.


        :param container_file: The container_file of this LaunchContainerBody.
        :type container_file: str
        """

        self._container_file = container_file

    @property
    def exec_command(self) -> str:
        """Gets the exec_command of this LaunchContainerBody.


        :return: The exec_command of this LaunchContainerBody.
        :rtype: str
        """
        return self._exec_command

    @exec_command.setter
    def exec_command(self, exec_command: str):
        """Sets the exec_command of this LaunchContainerBody.


        :param exec_command: The exec_command of this LaunchContainerBody.
        :type exec_command: str
        """

        self._exec_command = exec_command
