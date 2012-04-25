import re
from optparse import OptionParser

UA_PAT = re.compile(r'user_agent="(?P<ua>.*?)"')

# matches sequence: space, 2 char, - or _, 2 char, 0 or more ;, followed by char that's not a char, number, - or _
LOCALE_PAT = re.compile(r'(?P<locale> [a-zA-Z][a-zA-Z][-_][a-zA-Z][a-zA-Z];*)[^a-zA-Z0-9-_]')



def main():
    parser = OptionParser()
    parser.add_option('-i', '--input_file', dest='input_file')
    parser.add_option('-o', '--output_file', dest='output_file')
    (options, args) = parser.parse_args()
    
    if options.input_file is None or options.output_file is None:
        print "must specify both input file and output file"
        return
    
    with open(options.input_file, 'r') as in_f:
        with open(options.output_file, 'w') as out_f:
            for line in in_f:
                ua_match = UA_PAT.search(line)
                if ua_match:
                    ua = ua_match.group('ua')
                    
                    if not ua.startswith('DO_NOT'):
                        loc_match = LOCALE_PAT.search(ua)
                        if loc_match:
                            line = line.replace(loc_match.group('locale'), '')


                out_f.write(line)    
                        

if __name__ == '__main__':
    main()
