from optparse import OptionParser

def main():
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='file')
    parser.add_option('-v', '--verbose', action="store_true", dest='verbose')
    
    (options, args) = parser.parse_args()
    
    uniq_lines = set()
    freq_dict = {}
    line_count = 0
    
    with open(options.file, 'r') as in_f:
        for line in in_f:
            line_count += 1
            uniq_lines.add(line)
            if options.verbose:
                if line in freq_dict:
                    freq_dict[line] += 1
                else:
                    freq_dict[line] = 1

    with open(options.file+".deduped", 'w') as out_f:
        for line in uniq_lines:
            out_f.write(line)
    
    if options.verbose:
        for dup_line, dup_count in freq_dict.iteritems():
            if dup_count > 1:
                print "%i\t%s" %(dup_count, dup_line)

    print "total line count:", line_count
    print "uniq line count: ", len(uniq_lines)


if __name__ == "__main__":
    main()
