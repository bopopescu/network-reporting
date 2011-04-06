# This script uses Yelp's mrjob framework for local testing and simulation of MR.  
# Run this:
# > python [this script] < [input file path] > [output file path]
# Example:
# > python script.py < data/testlog.txt > data/testlog.out

from mrjob.job import MRJob

import uniq_user_mapper 


class UniqUserMRJob(MRJob):
    def mapper(self, key, line):
        for key, value in uniq_user_mapper.generate_kv_pairs(line):
            if key and value:
                yield key.replace('UniqValueCount:', ''), value
        
    def reducer(self, key, values):
        yield key, len(set(values))

    def steps(self):
        return [self.mr(self.mapper, self.reducer), ]


if __name__ == '__main__':
    UniqUserMRJob.run()
