import csv
import datetime
import logging

from django.http import HttpResponse
from google.appengine.ext import db

from common.constants import  *
from common.utils.pyExcelerator import *
#                   (  TABLE_FILE_FORMATS,
#                                ALL_STATS,
#                                REQ_STAT,
#                                IMP_STAT,
#                                CLK_STAT,
#                                CTR_STAT,
#                                CNV_STAT,
#                                CPA_STAT,
#                                CPM_STAT,
 #                               )

from reporting.models import SiteStats
from reporting.query_managers import SiteStatsQueryManager, StatsModelQueryManager
from reports.query_managers import ReportQueryManager

DT_TYPES = (datetime.datetime, datetime.time, datetime.date)
DEFAULT = 'default'

# Create a new excel workbook and add a sheet to it, return both
def open_xls_sheet():
    wbk = Workbook()
    wsht = wbk.add_sheet( 'Sheet 1' )
    return wbk, wsht

# Given a sheet and a line number, write a list of elements to that sheet
def write_xls_row( sheet, line, elts ):
    col = 0
    for elt in elts:
        if type(elt) in DT_TYPES:
            sheet.write(line, col, elt.isoformat())
        else:
            sheet.write(line, col, elt)
        col += 1

# Write a workbook to to_write ( file-like object )
def write_xls( to_write, wbk ):
    """
    This is essentially the 'save' function of pyExcelerator, but instead of
    writing to a file, we're writing to to_write (which should be an
    HttpResponse, which is a file-like object )
    """
    stream = wbk.get_biff_data()
    padding = '\x00' * ( 0x1000 - ( len( stream ) % 0x1000 ) )

    doc = CompoundDoc.XlsDoc()
    doc.book_stream_len = len( stream ) + len( padding )
    #apparently __method()'s are private.  Hacked to get around that
    doc.custom_save_stuff()

    #make file excessively large
    to_write.write( doc.header )
    to_write.write( doc.packed_MSAT_1st )
    #write data
    to_write.write( stream )
    #continue making file 200x bigger than needed
    to_write.write( padding )
    to_write.write( doc.packed_MSAT_2nd )
    to_write.write( doc.packed_SAT )
    to_write.write( doc.dir_stream )

# Take a Worksheet to write to and return a fucntion that takes a list as input and writes said list to input Worksheet
def make_row_writer( sheet ):
    #Because I don't want a function that just takes a list and writes it,
    #there's no reason I should have to keep track of lines
    global xls_line_cnt
    xls_line_cnt = 0
    def helper( elts ):
        global xls_line_cnt
        write_xls_row( sheet, xls_line_cnt, elts )
        xls_line_cnt += 1
        return
    return helper

# Takes the XLS workbook and returns a function which writes said book to a file-like object
def make_resp_writer( book ):
    def helper( resp ):
        write_xls( resp, book )
        return
    return helper

# returns a row writer and file-like object writer ( in this case the response )
def make_xls_writers():
    wbk, wsht = open_xls_sheet()
    return make_row_writer( wsht ), make_resp_writer( wbk )

# Creates a writer from the default csv writer and the response obj
# Returns a function that takes a list of values to write as comma separated
def write_csv_row( resp ):
    writer = csv.writer( resp )
    return writer.writerow

# Function for map, verifies that a stat is valid and then removes the _STAT part of it
def verify_stats( stat ):
    assert stat in ALL_STATS, "Expected %s to be an element of %s, it's not" % ( stat, ALL_STATS )
    return stat.split( '_STAT' )[0]

def write_stats( f_type, desired_stats, all_stats, site=None, owner=None,
        days=None, key_type=None):
    # make sure things are valid
    assert f_type in TABLE_FILE_FORMATS, "Expected %s, got %s" % \
            ( TABLE_FILE_FORMATS, f_type )
    response = None

    # setup response and writers
    if f_type == 'csv':
        response = HttpResponse( mimetype = 'text/csv' )
        row_writer = write_csv_row( response )
    elif f_type == 'xls':
        response = HttpResponse( mimetype = 'application/vnd.ms-excel' )
        row_writer, writer = make_xls_writers()
    else:
        # wat
        assert False, "This should never happen, %s is in %s but doens't" \
                "have an if/else case" % ( f_type, TABLE_FILE_FORMATS )

    start = days[0]
    end = days[-1]
    d_form = '%m-%d-%y'
    d_str = '%s--%s' % ( start.strftime( d_form ), end.strftime( d_form ) )
    if key_type == 'adgroup':
        key_type = 'campaign'
    owner_type = key_type.title()
    if site:
        fname = "%s_%s_%s.%s" % (owner_type, db.get(site).name, d_str, f_type)
    else:
        fname = "%s_%s.%s" % (owner_type, d_str, f_type)
    #should probably do something about the filename here
    response['Content-disposition'] = 'attachment; filename=%s' % fname

    # Verify requested stats and turn them into SiteStat attributes so we can
    # getattr them
    if key_type == 'ad_network':
        map_stats = desired_stats
    else:
        map_stats = map( verify_stats, desired_stats )

    # Title the columns with the stats that are going to be written
    row_writer( map_stats )

    #Write the data
    for stat in all_stats:
        # This is super awesome, we iterate over all the stats objects, since the "desired stats" are formatted
        # to be identical to the properties, we just use the list of requested stats and map it to get the right values
        row_writer( map( lambda x: getattr( stat, x ), map_stats ) )
    if f_type == 'xls':
        #excel has all the data in this temp object, dump all that into the response
        writer( response )
    return response

def write_ad_network_stats( f_type, stat_names, all_stats, days):
    # make sure things are valid
    assert f_type in TABLE_FILE_FORMATS, "Expected %s, got %s" % \
            ( TABLE_FILE_FORMATS, f_type )
    response = None

    # setup response and writers
    if f_type == 'csv':
        response = HttpResponse( mimetype = 'text/csv' )
        row_writer = write_csv_row( response )
    elif f_type == 'xls':
        response = HttpResponse( mimetype = 'application/vnd.ms-excel' )
        row_writer, writer = make_xls_writers()
    else:
        # wat
        assert False, "This should never happen, %s is in %s but doens't" \
                "have an if/else case" % ( f_type, TABLE_FILE_FORMATS )

    start = days[0]
    end = days[-1]
    d_form = '%m-%d-%y'
    d_str = '%s--%s' % ( start.strftime( d_form ), end.strftime( d_form ) )
    fname = "ad_network_%s.%s" % (d_str, f_type)
    #should probably do something about the filename here
    response['Content-disposition'] = 'attachment; filename=%s' % fname

    for network, network_stats in all_stats:
        if network_stats and network_stats['state'] == 2:
            row_writer( [network] )
            if network in stat_names:
                network_stat_names = stat_names[network]
            else:
                network_stat_names = stat_names[DEFAULT]

            row_writer(network_stat_names)
            logging.info('network_stats')
            logging.info(network_stats)
            row_writer([network_stats[stat] for stat in network_stat_names])
            app_stat_names = list(network_stat_names)
            app_stat_names.insert(0, 'name')
            row_writer(app_stat_names)
            for app in network_stats['sub_data_list']:
                row_writer([app[stat] for stat in app_stat_names])

    if f_type == 'xls':
        # excel has all the data in this temp object, dump all that into the
        # response
        writer( response )
    return response

def export_writer(file_type, file_name, row_titles, row_data):
    """ Creates a file, writes data to it, and returns an HttpResponse
    object for that file

    Args:
        file_type: string, type of file to be exported
        file_name: string, name of file to exported
        row_titles: list of strings, each string is
            a header for each row
        row_data: List of lists of strings, each list of strings is a row

    Returns:
        HttpResponse object that is a file to be saved by the user
    """
    if file_type == 'csv':
        response = HttpResponse(mimetype = 'text/csv')
        row_writer = write_csv_row( response )
    if file_type == 'xls':
        response = HttpResponse(mimetype = 'application/vnd.ms-excel')
        row_writer, writer = make_xls_writers()
    response['Content-disposition'] = 'attachment; filename=%s' % file_name
    row_writer(row_titles)
    for row in row_data:
        row_writer(row)
    if file_type == 'xls':
        writer(response)
    return response

def write_report(file_type, report_key, account):
    """ Writes a report with key report_key to a file of type file_type

    Args:
        file_type: xls or csv, type of file to be exported
        report_key: Key of report that is being exported,
            MUST BE REPORT.KEY NOT SCHEDULEDREPORT
        account: Key of account requesting the export

    Returns:
        An HTTPResponse with content disposition of a file
    """
    if file_type == 'csv':
        response = HttpResponse(mimetype = 'text/csv')
        row_writer = write_csv_row( response )
    if file_type == 'xls':
        response = HttpResponse(mimetype = 'application/vnd.ms-excel')
        row_writer, writer = make_xls_writers()
    report = ReportQueryManager(account).get_report_data_by_key(report_key)
    s_str = report.start.strftime('%m%d%Y')
    e_str = report.end.strftime('%m%d%Y')
    f_name = '%s %s-%s.%s' % (report.name, s_str, e_str, file_type)
    response['Content-disposition'] = 'attachment; filename=%s' % f_name
    stats_headers = ['Requests', 'Impressions', 'Clicks', 'Conversions']
    if report.report_blob:
        stats_headers += ['Revenue', 'CTR']
    headers = [report.d1.title()]
    if report.d2:
        headers.append(report.d2.title())
    if report.d3:
        headers.append(report.d3.title())
    headers += stats_headers
    row_writer(headers)
    for row in report.export_data:
        # Had to add this because fucked up unicode shit was fucking shit up, wierd if else because non-strings
        # don't need to be changed
        row_writer([elt.encode('ascii', 'ignore') if (isinstance(elt, str) or isinstance(elt, unicode)) else elt  for elt in row])

    if file_type == 'xls':
        writer(response)

    return response



