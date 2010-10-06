#!/usr/bin/env python
#
# Parses iTunes RSS feeds and generates a Google spreadsheet with the results
# of the Top 300 free apps in each Genre.
#
#
import feedparser
try:
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
import gdata.spreadsheet.service
import gdata.service
import atom.service
import gdata.spreadsheet
import atom
import getopt
import sys
import string
import time

SPREADSHEET_KEY = 't2qC_svKrmS6Ig2hit34Fhw'

class ITunesReader(object):
  
  def __init__(self, email, password, spreadsheet_key=SPREADSHEET_KEY):
    self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    self.gd_client.email = email
    self.gd_client.password = password
    self.gd_client.source = 'bd.py'
    self.gd_client.ProgrammaticLogin()
    
    self.spreadsheet_key = spreadsheet_key

    # All spreadsheets have worksheets. I think worksheet #1 by default always
    # has a value of 'od6'
    self.worksheet_id = 'od6'
    
  def populate_row(self, e = {}):
    # Prepare the dictionary to write
    d = {'title': e['title'],
      'summary': e['summary'][0:100],
      'id': e['id'],
      'artist': e['artist'],
      'releaseDate': e['releasedate'],
      'price': e['price'],
      'category': e['category'],
      'rights': e['rights']}

    entry = self.gd_client.InsertRow(d, self.spreadsheet_key, self.worksheet_id)
    if not isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
      print "Insert row failed."
      
  def genre(self, g=6000, n=300):
    url = "http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/topfreeapplications/sf=143441/limit=%d/genre=%d/xml" % (n, g)
    d = feedparser.parse(url)
    for e in d.entries:
      self.populate_row(e)
    
  def run(self):
    for g in range(6000, 6018):
      self.genre(g)
    
def main():
  # parse command line options
  try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "pw="])
  except getopt.error, msg:
    print 'python spreadsheetExample.py --user [username] --pw [password] '
    sys.exit(2)

  user = ''
  pw = ''
  key = ''
  # Process options
  for o, a in opts:
    if o == "--user":
      user = a
    elif o == "--pw":
      pw = a

  if user == '' or pw == '':
    print 'python spreadsheetExample.py --user [username] --pw [password] '
    sys.exit(2)

  sample = ITunesReader(user, pw)
  sample.run()

if __name__ == '__main__':
  main()