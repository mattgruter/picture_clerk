from __future__ import with_statement
import hashlib

def hashit(files, hashfunc):
    for path in files:
        with open(path, 'rb') as f:
            buf = f.read()
        f.closed

        h = hashfunc(buf)
        digest = h.hexdigest()

if __name__=='__main__':
    from timeit import Timer
    import os
    import fnmatch
    
    num_runs = 10
    
    path = './test_album'
    dirlist = os.listdir(path)
    files = fnmatch.filter(dirlist, "*.NEF")
    files = [ os.path.join(path, f) for f in files ]
    
    for algorithm in ('md5', 'sha1'):
        hashfunc = eval('hashlib.' + algorithm)
        print 'Timing', algorithm, '(' + hashfunc.__name__ + '):'
        print 'Hashing %i files' % len(files)
        t = Timer('hashit(files, hashfunc)', 'from __main__ import hashit, files, hashfunc')
        # Time hashit with given hashfunction num_runs times and print the minimum execution time
        exec_times = t.repeat(repeat=num_runs, number=1)
        print 'Minimal execution time out of %i runs: %.3f sec' % (num_runs, min(exec_times))
        print


 

