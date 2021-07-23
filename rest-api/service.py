# /1/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 22 14:53:23 2021

@author: Stephen Mooney
"""

import connexion
import os
import sys
from flask_cors import CORS
from waitress import serve

if __name__ == '__main__':
    cwd = os.getcwd()
    sys.path.append(cwd)
    parent = os.path.dirname(cwd)

    if parent not in sys.path:
        sys.path.append(parent)

    try:
        app = connexion.FlaskApp(__name__, specification_dir='specification')
        app.add_api('api-definition.yml')

        CORS(app.app)

        serve(app, host='0.0.0.0', port=9095)

    except Exception as ex:
        raise ex
