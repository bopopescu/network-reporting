
f = open('sample_data.final','r')

fno = 0
fn = 'parts/sample_data_part%03d.part'
curr_f = open(fn%fno, 'w')

for i, line in enumerate(f):
    if fno != i/10:
        fno += 1
        curr_f.close()
        curr_f = open(fn%fno, 'w')
    curr_f.write(line)
curr_f.close()
