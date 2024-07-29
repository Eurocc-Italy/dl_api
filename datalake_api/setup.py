# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "swagger_server"
VERSION = "1.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion == 2.14.2",
    "connexion[swagger-ui]",
    "python_dateutil == 2.6.0",
    "setuptools",
    "swagger-ui-bundle",
    "pymongo == 4.5.0",
    "urllib3 == 1.26",
    "dlaas-tui @ git+https://gitlab.hpc.cineca.it/eurocc/dl-tui",
    "boto3",
    "python-decouple",
    "python-dotenv",
    "python-jose",
]

setup(
    name=NAME,
    version=VERSION,
    description="DTaaS API",
    author_email="",
    url="",
    keywords=["Swagger", "DTaaS API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={"": ["swagger/swagger.yaml"]},
    include_package_data=True,
    entry_points={"console_scripts": ["swagger_server=swagger_server.__main__:main"]},
    long_description="""\
    This API handles the communication between the virtual infrastructure generated by the DTaaS codebase and the User. The goal is to allow to Upload, Updates, Donwload and Processing of data from a Dual S3/PFS Datalake thanks to interaction with a MongoDB. WARNING Asset is DECLARED but NEVER USED
    """,
)
