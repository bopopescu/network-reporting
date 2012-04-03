from common.utils.xlwt import Workbook
import datetime

def create_xls(*args, **kwargs):
    """
    Pass in kwargs like this:
    create_xls(apps=[app1, app2, app3],
               apps_fields=['name', 'start_datetime', 'end_datetime'],
               adunits=[adunit1, adunit2],
               adunits_fields=['name', 'app'])
    And out will come an excel file with:
    Name  Primary Field   Secondary Field
    =====================================
    App1  Entertainment   Games
    App2  Home            Gardening
    App3  Business        Networking

    Name     App
    =============
    AdUnit1  App1
    AdUnit2  App1
    """

    # Create a workbook and a sheet which we'll write data to
    wb = Workbook()
    if kwargs.has_key('title'):
        sheet = wb.add_sheet(str(title))
    else:
        sheet = wb.add_sheet('MoPub -- %s' % str(datetime.date.today()))

    # Find all of the headers. We'll use these to write column names
    # and to get data out of the objects that were passed in. If no
    # headers were passed in, then yer doin it wrong
    headers = {}
    for k in kwargs.keys():
        if k.find('_fields') > -1:
            headers.update({
                k: kwargs[k]
            })

    # We need at least one fields parameter
    if len(headers.keys()) == 0:
        raise ValueError('No fields were passed to create_xls among %s' \
                         % str(kwargs.keys()))

    # Make a list of all the rows we're going to write
    rows = []
    for header in headers.keys():
        # append the header row first
        rows.append(headers[header])
        # then append each object
        objs = kwargs.get(header.replace("_fields",""))
        for obj in objs:
            row = []
            for key in headers[header]:
                try:
                    row.append(getattr(obj, key))
                except AttributeError:
                    row.append(None)
            rows.append(row)

    print rows
        
            

def create_csv(*args, **kwargs):
    pass

def create_json(*args, **kwargs):
    pass

def create_xml(*args, **kwargs):
    pass