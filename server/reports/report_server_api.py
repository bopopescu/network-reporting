""" report_server_api.py

    Functions for communicating with the report server.
"""

import datetime
import logging
import urllib
import urllib2

try:
    import json
except:
    from django.utils import simplejson as json

from django.conf import settings


def _format_date(date):
    """Format datetime.date into string format accepted by reporting service."""
    date_with_time = datetime.datetime(date.year, date.month, date.day)
    return date_with_time.strftime('%Y-%m-%d %H:%M:%S')


def _report_server_http_call(url):
    """Make an HTTP get call to the given url (at the report server), and return the response."""
    request = urllib2.Request(url)
    request.add_header('Cookie', 'api_key=%s' % settings.REPORT_SERVER_SECRET_API_KEY)
    response = urllib2.urlopen(request).read()

    return response


def submit_report_request(report):
    """Submit a new report request to the reporting service."""
    report_schedule = report.schedule

    group_by_list = [g for g in [report_schedule.d1, report_schedule.d2, report_schedule.d3] if g]

    account_key = report.account.key()

    # Get the numeric ID for the account; can't use id() function alone because older keys might have a
    # numbered account encoded as a string.
    account_id = account_key.id_or_name()

    if not account_id:
        account_id = account_key

    # Reporting service takes both the account_id (an integer) and the account_key generated from the latter.
    # This is done because the key is too long for Postgres partition names.
    params = {
        'report_id': str(report.key()),
        'report_name': report_schedule.name,
        'requested_by': ', '.join(report_schedule.recipients),
        'account_num_id': str(account_id),
        'account_key': str(account_key),
        'group_by_list': ','.join(group_by_list),
        'start_time': _format_date(report.start),
        'end_time': _format_date(report.end)
    }

    logging.info('Sending request to report server: ' + str(params))

    submission_url = (
        'http://%s:%d/run_report?%s' %
        (settings.REPORT_SERVER_HOST, settings.REPORT_SERVER_PORT, urllib.urlencode(params)))

    try:
        response = _report_server_http_call(submission_url)
    except Exception, e:
        logging.warn("Couldn't contact report service: " + str(e))
    else:
        logging.info('Reponse from report server:' + response)


def get_report_data_url(report_data_callback_url):
    """Given a report ID, call back to the report server to get the signed S3 data URL."""

    full_url = (
        'http://%s:%s%s' %
        (settings.REPORT_SERVER_HOST, settings.REPORT_SERVER_PORT, report_data_callback_url))

    try:
        response = _report_server_http_call(full_url)
    except Exception, e:
        logging.warn("Couldn't contact report service to get data url: " + str(e))
        raise
    else:
        logging.info('Reponse from report server:' + response)

        response_json = json.loads(response)

        return response_json['url']
