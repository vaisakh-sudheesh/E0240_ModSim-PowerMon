import os
import sys
import glob
import io
## For handling BZ archive of result files
import tempfile
import tarfile
import datetime
import re
import csv
import pandas



#Temporary files/directories for handling data
tmpdir = tempfile.TemporaryDirectory()

def extract_data(data_archive:str) ->str:
    # TempDirectory to string returns something like ' <TemporaryDirectory ' prefixed
    ## for handling tmp directory cleanly, striping off these characters
    tmpfilePath = str(tmpdir).split(' ')[1].replace('\'','').replace('>','')
    print('Temporary directory created: '+tmpfilePath+'/')

    # Extract Files
    archive = tarfile.open(data_archive, 'r:bz2')
    # An assumption is made here that the archives are stored at directory level, than directly files
    # Hence getting the first level directory name 
    # e.g.: <TarInfo '11-03-2023_14-58-03_BigCore-10itr-50msSmplg-CPUFreq-2.0GHz' at 0x7fbc676ecd00>
    dirname=str(archive.getmembers()[0]).split(' ')[1].replace('\'','')

    archive.extractall(tmpfilePath+'/')
    archive.close()
    return os.path.join(tmpfilePath,dirname)

# Define regular expressions to match the lines with data
# Regular expression for [1] & [2], and associated result variable(s)
re_1_2_firstlevel = re.compile(r"""
                                ^    # Line start
                                [#]+ # Immediate occurance of '#'
                                .*   # Anything following that
                            """, re.X)
re_1_timestamp_info = re.compile(r"""
                                ^[#]+                 # Line Start with # character
                                \s+started\s+on\s+    # This string will be present before timestamp
                                (.*)                  # Time of perf start
                                """, re.X)


# Regular expression for [4]
re_4_summary_header = re.compile(r"""^\s+
                                Performance\scounter\sstats\sfor\s
                                \'(.*)\'\s+              # Type of monitoring in perf
                                \((\d+)\sruns\):
                                """,re.X)

# Regular expression for [3]
re_3_perf_stat_record = re.compile(r"""^\s+
                                (\d+\.\d+)\s+          # Timestamp
                                (\S+)\s+(\d+)\s+       # CPU-ID, CPUs
                                (.*)                   # counts, [unit], events, event-info
                                """, re.X)
re_3_subrec_countfield_nc = re.compile(r"""
                                    <not\scounted>\s+     # Is it a <not counted field> ?
                                    (.*)
                                    """, re.X)
re_3_subrec_countfield = re.compile(r"""
                                    (\d+[.\d]*)\s+        # counts
                                    (.*)              # units or event-name
                                    [#]+(.*)                  # Event extra info
                                    """, re.X)


def Process_ProfFile(proffile:str, outcsvfile:str) -> None:
    with io.open(proffile, 'rt') as  proffile_entry:
        
        stats_gatherer = {}
        perf_stat_starttime = ''
        perf_stat_starttime_dateobj = None
        perf_stat_currtime_dateobj = None
        perf_stat_columns = []
        perf_stat_runtype=''
        perf_stat_runcount=0


        records_ended = False
        record_counter = 0
        prev_timestamp =''
        rec_timestamp = rec_cpuid = rec_cpucnt = rec_counter = rec_eventname = ''
        csvout = open(outcsvfile, 'w') 
        csvwriter = None
        #Decoding the prof/perf-stat file data
        for line in proffile_entry.readlines():
            # print (str(len(line))+':'+line)

            ## Okay so, its a line starting with # character
            if re_1_2_firstlevel.match(line):
                # is it a time stamp info line??
                re_1_match = re_1_timestamp_info.match(line)
                if (re_1_match):
                    perf_stat_starttime = re_1_match.group(1)
                    perf_stat_starttime_dateobj = datetime.datetime.strptime(perf_stat_starttime,'%a %b %d %H:%M:%S %Y')
                    perf_stat_starttime_pddateobj = pandas.Timestamp(perf_stat_starttime_dateobj, unit='ns')
                    perf_stat_currtime_dateobj = datetime.datetime.strptime(perf_stat_starttime,'%a %b %d %H:%M:%S %Y')
                    perf_stat_currtime_pddateobj = pandas.Timestamp(perf_stat_currtime_dateobj)
                    print('Start Time:'+str(perf_stat_currtime_pddateobj))
                else:
                    # Then it must be a column header info line
                    perf_stat_columns = line[1:].split()
            else:
                # So its lines other than meta info ones ([1] & [2])
                # just to skip the last few records as we only need the perf-stat samples, not the summary at the end
                if (records_ended == False):
                    re_4_match = re_4_summary_header.match (line)
                    re_3_match = re_3_perf_stat_record.match(line)
                
                    if (re_4_match):
                        perf_stat_runtype  = re_4_match.group(1)
                        perf_stat_runcount = int(re_4_match.group(2))
                        records_ended = True
                        # Okay, so we have reached till the summary section
                        # write the last record
                        record_counter += 1
                        csvwriter.writerow(stats_gatherer)
                        stats_gatherer.clear()
                        
                    elif (re_3_match):
                        rec_timestamp = re_3_match.group(1)
                        rec_cpuid     = re_3_match.group(2)
                        rec_cpucnt    = re_3_match.group(3)


                        if (prev_timestamp==''):
                            prev_timestamp = rec_timestamp
                            ns = perf_stat_starttime_pddateobj+pandas.Timedelta(seconds=float(rec_timestamp))
                            # print('PDTime:'+str(ns)+' subsec: '+rec_timestamp)
                            stats_gatherer['utctime'] = ns

                        if (prev_timestamp != rec_timestamp):
                            ## Okay, we are encountering a new record, so dump the old one
                            record_counter += 1
                            if (record_counter == 1):
                                csvwriter =  csv.DictWriter(csvout, stats_gatherer.keys())
                                csvwriter.writeheader()
                            csvwriter.writerow(stats_gatherer)
                            stats_gatherer.clear()
                            prev_timestamp = rec_timestamp

                            ns = perf_stat_starttime_pddateobj+pandas.Timedelta(seconds=float(rec_timestamp))
                            # print('PDTime:'+str(ns)+' subsec: '+rec_timestamp)
                            stats_gatherer['utctime'] = ns

                        re3__ncsubrec_match = re_3_subrec_countfield_nc.match(re_3_match.group(4))

                        if (re3__ncsubrec_match):
                            trec = re3__ncsubrec_match.group(1)
                            # print (rec_cpuid + ' NC - '+trec)
                            stats_gatherer[rec_cpuid+'_'+trec] = 'NaN'
                            pass
                        else:

                            re_3_subrec_match = re_3_subrec_countfield.match(re_3_match.group(4))
                            if (re_3_subrec_match):
                                split_str =re_3_subrec_match.group(2).split() 
                                # print('event: '+re_3_subrec_match.group(1)+'-'+ split_str[len(split_str)-1] )
                                rec_counter = re_3_subrec_match.group(1)
                                rec_eventname = split_str[len(split_str)-1]
                            else:
                                ## Special cases, some instructions stats count seems to be having no '#' separator
                                ## Handle  it separately. e.g:
                                ##     808323      instructions                                                         (3.64%)
                                ##     52451588      instructions                                                         (8.98%)
                                ##     424251      instructions                                                         (8.92%)
                                ##     394060      instructions                                                         (8.86%)
                                tstr = re_3_match.group(4)
                                rec_counter   = tstr[0]
                                rec_eventname = tstr[1]
                                assert len(tstr) != 3,'Some invalid records structure found, please check!!!'
                                # print(re_3_match.group(4))

                            if (rec_eventname == 'cpu-clock'):
                                stats_gatherer[rec_cpuid+'_'+rec_eventname] = float(rec_counter)
                            else:
                                stats_gatherer[rec_cpuid+'_'+rec_eventname] = int(rec_counter)
                                
                else:
                    ## For now, we are only going to process the individual records, not the summary
                    ## So we can very well break out of the loop
                    break


        print ('Start time: '+ perf_stat_starttime)
        print ('Columns: '+ str(perf_stat_columns))
        print ('runs type: '+ perf_stat_runtype)
        print ('runs count: '+ str(perf_stat_runcount) )
        print ('Total Records: '+ str(record_counter) )


data_dir='/home/vaisakh/developer/modeling/tmp/extract/'

# outdir = extract_data(prof)
in_data_prof=os.path.join(data_dir,'IdleSleep-perf-1.prof')
in_data_power=os.path.join(data_dir,'IdleSleep-perf-1.powdata')
in_data_polldata=os.path.join(data_dir,'IdleSleep-perf-1.polldata')

out_prof_csv = os.path.join(data_dir,'IdleSleep-perf-1.prof.csv')
Process_ProfFile(in_data_prof,out_prof_csv)




