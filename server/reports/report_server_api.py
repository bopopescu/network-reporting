""" report_server_api.py

    Functions for communicating with the report server.
"""

import datetime
import logging
import urllib

try:
    import json
except:
    from django.utils import simplejson as json

from django.conf import settings


def format_date(date):
    """Format datetime.date into string format accepted by reporting service."""
    date_with_time = datetime.datetime(date.year, date.month, date.day)
    return date_with_time.strftime('%Y-%m-%d %H:%M:%S')


def submit_report_request(report):
    """Submit a new report request to the reporting service."""
    report_schedule = report.schedule

    group_by_list = [g for g in [report_schedule.d1, report_schedule.d2, report_schedule.d3] if g]

    account_key = report.account.key()
    account_id = account_key.id()

    if not account_id:
        account_id = account_key

    # Reporting service takes both the account_id (an integer) and the account_key generated from the latter.
    # This is done because the key is too long for Postgres partition names.
    params = {
        'report_id': str(report.key()),
        'account_num_id': str(account_id),
        'account_key': str(account_key),
        'group_by_list': ','.join(group_by_list),
        'start_time': format_date(report.start),
        'end_time': format_date(report.end)
    }

    logging.info('Sending request to report server: ' + str(params))

    submission_url = (
        'http://%s:%d/run_report?%s' %
        (settings.REPORT_SERVER_HOST, settings.REPORT_SERVER_PORT, urllib.urlencode(params)))

    try:
        response = urllib.urlopen(submission_url).read()
        logging.info('Reponse from report server:' + response)
    except Exception, e:
        logging.warn("Couldn't contact report service: " + str(e))


def get_report_data_url(report_id):
    """Given a report ID, call back to the report server to get the signed S3 data URL."""
    report_url = (
        'http://%s:%d/report_results/%s?mode=link' %
        (settings.REPORT_SERVER_HOST, settings.REPORT_SERVER_PORT, report_id))
    response = urllib.urlopen(report_url).read()
    logging.info('Reponse from report server:' + response)

    response_json = json.loads(response)

    return response_json['url']
