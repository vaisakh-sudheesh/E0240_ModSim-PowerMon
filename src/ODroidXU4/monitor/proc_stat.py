#!/usr/bin/env python3
import fabric
import re

class ProcStatSampler:
    '''Wrapper class for /proc/stat sampling

    Processing only the cpu time stats, will be helpful in modeling CPU Usage statistics.
    More information about /proc/stat can be found in https://man7.org/linux/man-pages/man5/proc.5.html

    Sample output of /proc/stat file:
        #
        # root@odroid:~# cat /proc/stat 
        # cpu  66364 14 11625 6728970 828 16650 1549 0 0 0
        # cpu0 13857 0 2112 834694 300 1673 358 0 0 0
        # cpu1 6299 0 1962 840515 236 1477 298 0 0 0
        # cpu2 11519 14 1964 837576 149 1349 165 0 0 0
        # cpu3 6864 0 5363 839026 141 1359 232 0 0 0
        # cpu4 2 0 29 851565 0 2497 2 0 0 0
        # cpu5 0 0 21 851622 0 2489 2 0 0 0
        # cpu6 0 0 81 850175 0 3210 477 0 0 0
        # cpu7 27821 0 88 823794 0 2594 12 0 0 0
        # ....
        #
    '''
    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn
        self.__csv_header__ = 'stat_cpuid,'\
                              'stat_user,stat_nice,stat_system,stat_idle,stat_iowait,'\
                              'stat_irq,stat_steal,stat_guest,stat_guest_nice'
        self.__csv_fieldcnt__ = len(self.__csv_header__.split(','))
    
    def header(self):
        '''Returns header to be used for CSV file
        '''
        return self.__csv_header__


    def sample_data(self) -> [str]:
        '''Returns list of timestamp-ed(utc & local) csv strings to be recorded 
        '''
        cpustat  = self.__conn__.run('cat /proc/stat', hide='stdout')
        
        if cpustat:
            cpustat_stdout = cpustat.tail('stdout',16).strip().splitlines()
            res = []
            ctr = 0
            for line in cpustat_stdout:
                csved = re.sub(' +', ',', line)
                test_len = len(csved.split(','))
                # validating CSV-ed CPU stats
                assert test_len == 11, 'Processed length of elements of /proc/stat seems to be wrong as '+\
                                        str(test_len) + ', expected 11'
                
                test_len = len(csved.split(','))
                # validating final CSV length
                assert test_len == (self.__csv_fieldcnt__ + 1), 'Final length of CSV record seems to be wrong as '\
                                            +str(test_len)+\
                                            ', expected: '+str(self.__csv_fieldcnt__)
                res.append(csved)
                # Since we are extracting only CPU time/stat entries, exit after 8 lines
                ctr += 1
                if (ctr > 8):
                    break
            return res
        else:
            return []
        
#### ==========================================================================
#### Test Code
if __name__ == '__main__':
    import time
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    procstat = ProcStatSampler(conn)
    
    csv_header = procstat.header()
    print('CSV Header: '+csv_header)
    ##TODO: Add assertion for testing csv formatted data of N number of fields

    procstat_cpu = procstat.sample_data()
    print(procstat.sample_data())
    
    ##TODO: Add assertion for testing csv formatted data of N number of fields
    
    print ('Proc Stat test completed...')

#### ==========================================================================