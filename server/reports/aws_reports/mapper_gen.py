F_NAME = '%s_%s_%s_report_mapper.py'
DIMS = (None, 
        'app', 
        'adunit', 
        'campaign', 
        'creative', 
        'priority', 
        'month', 
        'week', 
        'day', 
        'hour', 
        'country', 
        'marketing', 
        'brand', 
        'os', 
        'os_ver', 
        'kw')


for dim1 in DIMS:
    if dim1 is None:
        continue
    for dim2 in DIMS:
        if dim1 == dim2:
            continue
        for dim3 in DIMS:
            if dim1 == dim3 or (dim2 == dim3 and dim2 is not None):
                continue
            if dim2 is None and dim3 is not None:
                continue
            f = open("report_mapper.py", 'r')
            f2 = open(F_NAME % (dim1, dim2, dim3), 'w')
            for i, line in enumerate(f.readlines()):
                if i == 9:
                    f2.write("D1 = '%s'\n" % dim1)
                    if dim2 is None:
                        f2.write("D2 = %s\n" % dim2)
                    else:
                        f2.write("D2 = '%s'\n" % dim2)
                    if dim3 is None:
                        f2.write("D3 = %s\n" % dim3)
                    else:
                        f2.write("D3 = '%s'\n" % dim3)
                f2.write(line)
            f2.close()
            f.close()
