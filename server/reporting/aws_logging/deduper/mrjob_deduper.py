# This script uses Yelp's mrjob framework for local testing and simulation of MR.  
# Run this:
# > python [this script] < [input file path] > [output file path]
# Example:
# > python script.py < data/testlog.txt > data/testlog.out

from mrjob.job import MRJob


class LogDeduperMRJob(MRJob):
    def mapper(self, key, line):
        yield line, 1

    def reducer(self, line, occurrences):
        yield line, sum(occurrences)

    def steps(self):
        return [self.mr(self.mapper, self.reducer), ]


if __name__ == '__main__':
    LogDeduperMRJob.run()
