#!/usr/bin/env python3

import fabric
import time
import os
import datetime

## Import the local packages
from pathlib import Path
import sys
path_root = Path(__file__).parents[0]
sys.path.append(str(path_root))
print (str(path_root))

# import data samplers
import monitor.thermal as therm
import monitor.proc_stat as pstat

class DataSampler:
    def __init__(self, conn: fabric.Connection):
        self.__conn__ = conn
        # initialize the sampler objects
        self.__thermal__  = therm.ThermalSampler (self.__conn__)
        self.__procstat__ = pstat.ProcStatSampler(self.__conn__)

        # Combined CSV Header 
        self.__combined_header__ = \
                    'ts_utc,ts_local,'+\
                    self.__thermal__.header()+','+\
                    self.__procstat__.header()
        # Helpful in validation
        self.__combined_header_len__ = len(self.__combined_header__.split(','))
    
    def header(self):
        '''Returns header to be used for CSV file
        '''
        return self.__combined_header__


    def sample_data(self) -> [str]:
        # Get current timestamps for record
        utcts  = datetime.datetime.utcnow()
        locats = datetime.datetime.now()
        csv_record = []
        procdata = self.__procstat__.sample_data()
        for entry in procdata:
            rec = str(utcts) + ',' + str(locats) + ',' +\
                    self.__thermal__.sample_data() + ',' +\
                    entry
            csv_record.append(rec)    

        return csv_record


if __name__ == '__main__':
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    ds = DataSampler(conn)

    csv_header = ds.header()
    print('CSV Header: '+csv_header)
    ##TODO: Add assertion for testing csv formatted data of N number of fields

    data = ds.sample_data()
    print(data)
    ##TODO: Add assertion for testing csv formatted data of N number of fields

    print ('Proc Stat test completed...')

#### ==========================================================================