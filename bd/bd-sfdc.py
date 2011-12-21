#!/usr/bin/env python
#
# Parses iTunes RSS feeds and creates Lead objects in SFDC for each of the applications
# discovered. 
#
# Usage: ./bd-sfdc.py --user jim@mopub.com --pw fhaaCohb2SbVB0IFXhsseGfJ3Onr9UA46
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
import beatbox

class Company(object):
    def __init__(self, name):
        self.name = name.encode("utf-8")
        self.apps = []
    
    def add_app(self, app):
        self.apps = (self.apps or []) + [app]
        
    def to_sfdc(self, feed_type):
        categories = [a.get('category') for a in self.apps]
        return {'Company': self.name, 
                'FirstName': "A", 'LastName': "Developer",
                'LeadSource': 'AppStoreCrawl', 
                'Number_of_Apps__c': len(self.apps),
                'Apps__c': "\n".join(["%s (#%d in %s)" % (a.get("title"), a.get("rank"), a.get("category")) for a in self.apps]),
                'iTunesURL__c': max([a.get("url") for a in self.apps]),
                'Top_Rank__c': min(a.get('rank') for a in self.apps),
                'Primary_Category__c': max(set(categories), key=categories.count),
                'iTunes_Artist_Name__c': max([a.get('artist') for a in self.apps]),
                'iTunes_Feed_Type__c': feed_type,
                'HtmlSummary__c': "<hr/>".join([a.get('summary') for a in self.apps]),
                'Description': '',
                'type': 'Lead'}

    def __repr__(self):
        return "%s [%d apps]" % (str(self.name), len(self.apps))

class ITunesReader(object):
    
    FEED_TYPES = ["topfreeipadapplications", "newfreeapplications", "topfreeapplications"]

    def __init__(self, feed_type):
      self.feed_type = feed_type
      self.companies = {}    
      
    def populate_row(self, n, e = {}):
        title = e.get('title')
        app_name = title.split(" - ")[0]
        company_name = title.split(" - ")[1]
        
        # Prepare the dictionary to write
        app = {'title': app_name,
               'artist': e.get('artist') or '',
               'summary': (e.get('content')[0].get('value') or ''),
               'url': e.get('id'),
               'category': e.get('category'),
               'rank': n}
        
        # Find company
        company = self.companies.get(e.get('artist')) or Company(company_name)
        company.add_app(app)
        
        # Set back into hash
        self.companies[e.get('artist')] = company

    def genre(self, g, n):
        url = "http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/%s/sf=143441/limit=%d/genre=%d/xml" % (self.feed_type, n, g)
        d = feedparser.parse(url)
        i = 1
        for e in d.entries:
            self.populate_row(i, e)
            i += 1

    def run(self, genres=range(6000, 6018), n=300):
        for g in genres:
            self.genre(g, n)
        return self.companies
        
    
def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "pw="])
    except getopt.error, msg:
        print 'python bd-sfdc.py --user [username] --pw [password] '
        sys.exit(2)

    user = ''
    pw = ''
    n = 2
    # Process options
    for o, a in opts:
        if o == "--user":
            user = a
        elif o == "--pw":
            pw = a
        elif o == "--max":
            n = int(a)

    if user == '' or pw == '':
        print 'python bd-sfdc.py --user [username] --pw [password] --max [count]'
        sys.exit(2)

    for c in ITunesReader.FEED_TYPES:
        print 'Crawling %s...' % c
        
        # Start up iTunes reader
        reader = ITunesReader(c)
        companies = reader.run(range(6000, 6018), n).values()
    
        # Save these into SFDC objects
        sforce = beatbox.PythonClient()
        try:
            login_result = sforce.login(user, pw)
        except beatbox.SoapFaultError, errorInfo:
            print "Login failed: %s %s" % (errorInfo.faultCode, errorInfo.faultString)
            return
    
        # Create the new leads...  
        while len(companies) > 0:
            try:
                create_result = sforce.upsert('iTunes_Artist_Name__c', [v.to_sfdc(reader.feed_type) for v in companies[:200]])
                print create_result
            except:
                print "Could not insert some records in this batch."
            companies[:200] = []
    
if __name__ == '__main__':
    main()