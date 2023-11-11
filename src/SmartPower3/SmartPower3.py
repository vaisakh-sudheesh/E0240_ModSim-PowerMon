#!/usr/bin/env python3
import socket
import csv
import datetime
import threading
import select

###############################################################################
# Utility class for processing UDP packet of power readings
###############################################################################
class NCSampler:

    """
    Ref: https://wiki.odroid.com/accessory/power_supply_battery/smartpower3#logging_protocol
    """
    pd_col_info = [
        ## Time fields - UTC, Local and Milliseconds logged by SmartPower3
        'utctime','localtime','sm_mstime',
        ## Input Power parameters of SmartPower's power supply
        'ps_ippwr-volts_mV','ps_ippwr-ampere_mA','ps_ippwr-watt_mW','ps_ippwr-status_b',
        ## Channel-0's output supply parameters and status
        'dev_ippwr-ch0-volts_mV', 'dev_ippwr-ch0-ampere_mA', 'dev_ippwr-ch0-watt_mW', 
        'dev_ippwr-ch0-status_b', 'dev_ippwr-ch0-interrupts',
        ## Channel-1's output supply parameters and status
        'dev_ippwr-ch1-volts_mV', 'dev_ippwr-ch1-ampere_mA','dev_ippwr-ch1-watt_mW', 
        'dev_ippwr-ch1-status_b', 'dev_ippwr-ch1-interrupts',
        ## Checksum fields
        'crc8-2sc', 'crc8-xor'
    ]
    
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0',6000))
        self.sock.setblocking(0)
        self.bExit = False
        self.f = None
        self.sampling_thread = None

    def __del__(self) -> None:
        print('Cleaning NC')
        self.sock.shutdown()
        self.sock.close()
        
    

    def __ProcessPacket(self)-> None:
        """Function to process each packets"""
        try:
            while (self.bExit == False):
                ready = select.select([self.sock], [], [], 1)
                if ready[0]:
                    data, _ = self.sock.recvfrom(81)
                    fields = data.strip().split(b',')
                    row = [datetime.datetime.utcnow()]+[datetime.datetime.now()]+fields
                    self.writer.writerow(row)
        except socket.timeout:
            print("\nerror: socket timeout")
    
    def StartSampling(self, filename:str)->None:
            self.bExit = False
            self.f = open(filename, "w", newline="")
            self.writer = csv.writer(self.f)
            self.writer.writerow(self.pd_col_info)

            self.sampling_thread = threading.Thread(target = self.__ProcessPacket)
            self.sampling_thread.start()
            print ('SM3-NCSampler: thread started and logging in to '+filename)

    def StopSampling(self,)->None:
        self.bExit = True
        self.sampling_thread.join()
        self.f.close()
        self.f = None
        self.writer = None
        print ('SM3-NCSampler: thread stopped')
