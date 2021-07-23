#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 17:59:14 2021

@author: Stephen Mooney
"""
import flask
import gc
import json
import os
import pandas as pd
import pytz
import requests
import sys

from datetime import datetime
from http import HTTPStatus

OK_STATUS_CODE = HTTPStatus.OK.value
TZ_GIVEN = 'America/Detroit'


class WireDownAPI(object):
    """
    """

    def __init__(self):
        self.results_df = None

    def ready(self):
        req_time = self._get_datetime_string()
        response = dict(time=req_time, status="Ready", message="Model is loaded and ready for scoring.")
        res_status = OK_STATUS_CODE

        return response, res_status

    """
    """

    def wiredown_likelihood_request(self):
        self.results_df = pd.read_excel('mock_data/mock_data.xlsx')
        self.results_df.columns = map(str.lower, self.results_df.columns)
        self.results_df.event_creation_time = pd.to_datetime(self.results_df.event_creation_time)
        self.results_df['event_creation_time'] = self.results_df.event_creation_time.dt.strftime('%Y-%m-%d @ %H:%M:%S')
        # self.results_df.event_creation_time.strftime('%Y-%m-%d @ %H:%M:S')

        qqq = self.results_df.to_json(orient='records')
        print(qqq)

        return json.loads(self.results_df.to_json(orient='records'))

    """
    """

    def health(self):
        req_time = self._get_datetime_string()
        response = dict(time=req_time, status="Healthy", message="App is running.")
        res_status = OK_STATUS_CODE

        return response, res_status

    """
    """

    def _get_datetime_string(self, tz_given=TZ_GIVEN):
        utc_time = datetime.utcnow()
        tz_given = pytz.timezone(tz_given)
        dt = utc_time + tz_given.utcoffset(utc_time)
        return datetime.strftime(dt, '%Y-%m-%d @ %H:%M (%Z)')

    """
    """

    def __refresh_data(self):
        None


class_instance = WireDownAPI()
