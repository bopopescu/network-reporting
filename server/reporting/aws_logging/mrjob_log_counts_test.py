# This script uses Yelp's mrjob framework for local testing and simulation of MR.  
# Run this:
# > python [this script] < [input file path] > [output file path]
# Example:
# > python script.py < data/testlog.txt > data/testlog.out

from mrjob.job import MRJob

import basic_log_mapper 
import log_reducer 


def sum_up(counts):
    cumulative_counts = None
    for c in counts:
        if cumulative_counts is None:
            cumulative_counts = c
        else:
            cumulative_counts = log_reducer.update_counts(cumulative_counts, c)
    return cumulative_counts


class LogCountMRJob(MRJob):
    def mapper(self, key, line):
        hour_k, hour_v, date_k, date_v = basic_log_mapper.generate_kv_pairs(line)
        if hour_k and hour_v and date_k and date_v:
            yield hour_k, eval(hour_v)
            yield date_k, eval(date_v)

    def reducer(self, key, values):
        yield key, sum_up(values)

    def steps(self):
        return [self.mr(self.mapper, self.reducer), ]


if __name__ == '__main__':
    LogCountMRJob.run()
