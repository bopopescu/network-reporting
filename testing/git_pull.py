import subprocess

def main():
    p = subprocess.Popen(['pushd','~/Desktop/mopub'], 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT)
    
    p = subprocess.Popen('git pull', 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        print "PYTHON:",line,
    retval = p.wait()
    

if __name__ == "__main__":
    main()