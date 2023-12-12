#!/usr/bin/env python3

import connexion
import os
from swagger_server import encoder
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'handlers': {
        'syslog': {
        'class': 'logging.handlers.SysLogHandler'
        }
    },
    'root': {
       'handlers': ['syslog']
    }
})

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.logger.warn("I configured the flask logger!")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'DTaaS API'}, pythonic_params=True)
    app.run(debug=True,port=8080)


if __name__ == '__main__':
    main()
