# This script uses Yelp's mrjob framework for local testing and simulation of MR.  
# Run this:
# > python [this script] < [input file path] > [output file path]
# Example:
# > python script.py < data/testlog.txt > data/testlog.out

from mrjob.job import MRJob

import preprocess_mapper 
# import log_reducer 


# def sum_up(counts):
#     cumulative_counts = None
#     for c in counts:
#         if cumulative_counts is None:
#             cumulative_counts = c
#         else:
#             cumulative_counts = log_reducer.update_counts(cumulative_counts, c)
#     return cumulative_counts


class PreprocessMRJob(MRJob):
    def mapper(self, key, line):
        parts = line.split('\t')
        if len(parts) == 2:        
            line = parts[0] 
            pp_line = preprocess_mapper.preprocess_logline(line)
            if pp_line:
                yield pp_line, 1


    def reducer(self, key, values):
        yield key, sum(values)


    def steps(self):
        return [self.mr(self.mapper, self.reducer), ]


if __name__ == '__main__':
    PreprocessMRJob.run()
