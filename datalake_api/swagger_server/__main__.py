#!/usr/bin/env python3

import connexion
import os
from swagger_server import encoder


def main():
    #opening at main project directory
    os.chdir('/home/centos/dtaas_test_api/')

    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'DTaaS API'}, pythonic_params=True)
    app.run(debug=True,port=8080)


if __name__ == '__main__':
    main()
