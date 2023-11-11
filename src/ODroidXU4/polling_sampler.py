#!/usr/bin/env python3

import fabric
import time
import os
import threading
import datetime
import csv

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
        self.__combined_header__ = ['ts_utc','ts_local']
        self.__combined_header__ += self.__thermal__.header()
        self.__combined_header__ += self.__procstat__.header()

        # Helpful in validation
        self.__combined_header_len__ = len(self.__combined_header__)

        self.bExit = False
        self.f = None
        self.sampling_thread = None
    
    def __header__(self) -> [str]:
        '''Returns header to be used for CSV file
        '''
        return self.__combined_header__


    def __sample_data__(self) -> [str]:
        # Get current timestamps for record
        utcts  = datetime.datetime.utcnow()
        locats = datetime.datetime.now()
        csv_record = []
        procdata = self.__procstat__.sample_data()
        for entry in procdata:
            rec = [str(utcts), str(locats)] + self.__thermal__.sample_data() + entry
            csv_record.append(rec)    
        return csv_record
    
    def __poll__(self) -> None:
        while (self.bExit == False):
            row = self.__sample_data__()
            self.writer.writerows(row)
            time.sleep(2)
    
    def StartSampling(self, filename:str)->None:
        self.bExit = False
        self.f = open(filename, "w", newline="")
        self.writer = csv.writer(self.f)
        self.writer.writerow(self.__header__())

        self.sampling_thread = threading.Thread(target = self.__poll__)
        self.sampling_thread.start()

    def StopSampling(self,)->None:
        self.bExit = True
        self.sampling_thread.join()
        self.f.close()
        self.f = None
        self.writer = None


if __name__ == '__main__':
    conn = fabric.Connection( '192.168.0.101', port=22, user='root', connect_kwargs={'password':'odroid'})
    ds = DataSampler(conn)

    csv_header = ds.__header__()
    print('CSV Header: '+str(csv_header))
    ##TODO: Add assertion for testing csv formatted data of N number of fields
    assert len(csv_header) == ds.__combined_header_len__, 'Header length seems to be mismatching. Expected'+\
        str(ds.__combined_header_len__)+', obtained'+str(len(csv_header))

    data = ds.__sample_data__()
    print(str(data))
    assert (len(data[0]) - 1) == ds.__combined_header_len__, 'Data length seems to be mismatching. Expected'+\
        str(ds.__combined_header_len__)+', obtained'+str(len(data[0]))
    ##TODO: Add assertion for testing csv formatted data of N number of fields

    # ds.StartSampling('testoutput.cpustats')
    # time.sleep(15)
    # ds.StopSampling()

    print ('Proc Stat test completed...')

#### ==========================================================================