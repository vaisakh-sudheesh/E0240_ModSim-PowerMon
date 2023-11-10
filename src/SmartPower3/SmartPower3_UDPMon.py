#!/usr/bin/env python3
"""Module for handling power data reading from SmartPower3 Monitor via UDP

This module has utility classes and asynchronous data sampling helper 
functions. More information SmartPower3 unit can be found in SmartPower3
wiki URL:
     https://wiki.odroid.com/accessory/power_supply_battery/smartpower3

Author(s): 
 - Vaisakh P S <vaisakhp@iisc.ac.in>
Date: 29-10-2023

Assumptions:
  (1) It is assumed that the SmartPower3 monitor is already pre-configured with
      required configuration. such as:
        (a) IP & port Configuration if the machine wherein this script is expected
            to sample data
        (b) Appropriate sampling configuration

Limitations:
  N/A

Warnings:
  N/A

TODO:
  (1) Fully automate necessary setting of all required configuration parameters to 
      SmartPower3 device including IP, Port, etc.

"""

import socket
import csv
import datetime
import time
import threading
import asyncio
import select

from enum import IntEnum

###############################################################################
# Utility class for processing UDP packet of power readings
###############################################################################

class SmartPower3_NCSampler:

    """
    Ref: https://wiki.odroid.com/accessory/power_supply_battery/smartpower3#logging_protocol
    """
    pd_col_info = [
      'utctime',
      'sm_mstime',
      'ps_ippwr-volts_mV','ps_ippwr-ampere_mA','ps_ippwr-watt_mW','ps_ippwr-status_b',
      'dev_ippwr-ch0-volts_mV', 'dev_ippwr-ch0-ampere_mA', 'dev_ippwr-ch0-watt_mW', 
          'dev_ippwr-ch0-status_b', 'dev_ippwr-ch0-interrupts',
      'dev_ippwr-ch1-volts_mV', 'dev_ippwr-ch1-ampere_mA','dev_ippwr-ch1-watt_mW',
          'dev_ippwr-ch1-status_b', 'dev_ippwr-ch1-interrupts',
      'crc8-2sc', 'crc8-xor'
    ]
    
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0',6000))
        self.sock.setblocking(0)
        self.bExit = False
        self.f = None
        self.write = None
        self.sampling_thread = None
    

    def __ProcessPacket(self)-> None:
        """Function to process each packets, this will wait indefinitely until interrupted"""
        print("\nWaiting for data samples")
        try:
            while (self.bExit == False):
                ready = select.select([self.sock], [], [], 1)
                if ready[0]:
                    data, _ = self.sock.recvfrom(81)
                    fields = data.strip().split(b',')
                    row = [datetime.datetime.now()]+fields
                    self.writer.writerow(row)
                    print("\ndebug: packet received: "+str(row))
        except socket.timeout:
            print("\nerror: socket timeout")
    
    def StartSampling(self, filename:str)->None:
            self.bExit = False
            self.f = open(filename, "w", newline="")
            self.writer = csv.writer(self.f)
            self.writer.writerow(self.pd_col_info)

            self.sampling_thread = threading.Thread(target = self.__ProcessPacket)
            self.sampling_thread.start()
            print ("Sampling started")

    def StopSampling(self,)->None:
        self.bExit = True
        self.sampling_thread.join()
        print ("Sampling stopped and data written")
        self.f.close()
        self.f = None
        self.writer = None

if __name__ == "__main__":
    net = SmartPower3_NCSampler()
    print ("Starting sampling")
    net.StartSampling('sampled_data.csv')
    print ("Waiting..")
    time.sleep(10) 
    print ("Stopping sampling..")
    net.StopSampling()
    # writer.writerow(row)
    
    