import csv

from common.constants import  *
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

from common.utils.pyExcelerator import * 
from django.http import HttpResponse
from reporting.models import SiteStats
from reporting.query_managers import SiteStatsQueryManager

# Create a new excel workbook and add a sheet to it, return both
def open_xls_sheet():
    wbk = Workbook()
    wsht = wbk.add_sheet( 'Sheet 1' )
    return wbk, wsht

# Given a sheet and a line number, write a list of elements to that sheet
def write_xls_row( sheet, line, elts ):
    col = 0
    for elt in elts:
        sheet.write( line, col, elt )
        col += 1

# Write a workbook to to_write ( file-like object )
def write_xls( to_write, wbk ):
    #This is essentially the 'save' function of pyExcelerator, but instead of writing
    #to a file, we're writing to to_write (which should be an HttpResponse, which is a file-like object )
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

def write_stats( f_type, desired_stats, site=None, owner=None, days=None ):
    #make sure things are valid
    assert f_type in TABLE_FILE_FORMATS, "Expected %s, got %s" % ( TABLE_FILE_FORMATS, f_type )
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
        assert False, "This should never happen, %s is in %s but doens't have an if/else case" % ( f_type, TABLE_FILE_FORMATS )

    all_stats = SiteStatsQueryManager().get_sitestats_for_days( site=site, owner=owner,days=days )
    owner = None
    for i in range( len( days ) ):
        if owner is None and all_stats[i].owner is not None:
            owner = all_stats[i].owner
        elif owner is None and all_stats[i].site is not None:
            owner = all_stats[i].site
        all_stats[i].date = days[i]
    import logging
    for s in all_stats:
        logging.info( all_stats )
    owner_type = owner.key().kind()
    if owner_type == 'Site':
        owner_type = 'AdUnit'
    owner_name = owner.name

    start = days[0]
    end = days[-1]
    d_form = '%m%d%y' 
    d_str = '%s-%s' % ( start.strftime( d_form ), end.strftime( d_form ) )
   
    fname = "%s_%s_%s.%s" % ( owner_name, owner_type, d_str, f_type )
    #should probably do something about the filename here
    response['Content-disposition'] = 'attachment; filename=%s' % fname 

    #Verify requested stats and turn them into SiteStat attributes so we can getattr them
    map_stats = map( verify_stats, desired_stats )


    #write a header row.  Right now this will look EXACTLY like how the accessors look, Might want to clean this
    row_writer( map_stats )
    
    #Write the data
    for stat in all_stats:
        # This is super awesome, we iterate over all the stats objects, since the "desired stats" are formatted
        #   to be identical to the properties, we just use the list of requested stats and map it to get the right values
        row_writer( map( lambda x: getattr( stat, x ), map_stats ) )
    if f_type == 'xls':
        #excel has all the data in this temp object, dump all that into the response
        writer( response )
    return response
        

        

