**Commit-SHA:** 348c8030600b8773faa90d7f126b0af12bfc9daf

## Hardware configuration
- Memory Controller max frequency & simple_ondemand -> performance governor
- CPU Frequency governor set to performance
- Fan at max speed always
- CPU Isolation

## Data gathering 
- CPU Frequency stepping (Big and little cores)
- Polling data gathered for thermal and CPU utilization ad
- Perf sampling at 100ms
- Power data sampling at 50ms

## Workloads Executed

Frequencies

- bigcore_freq_list    = [1800000, 1600000, 1400000, 1200000]
- littlecore_freq_list = [1400000, 1200000, 1000000, 800000 ]

**Iterations:** 3
```python
        ##################### Stress workloads - BEGIN ######################
        if (self.enable_stress_workloads == True):
            ### ------------ CPU Only workloads ------------ 
            self.workload_listing.append(WorkloadRecord('stress-cpu1-100s', 'stress','-c 1 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu2-100s', 'stress','-c 2 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu3-100s', 'stress','-c 3 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-cpu4-100s', 'stress','-c 4 -t 100s'))
            ### ------------ IO Only workloads ------------ 
            self.workload_listing.append(WorkloadRecord('stress-io1-100s', 'stress','-i 1 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-io2-100s', 'stress','-i 2 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-io3-100s', 'stress','-i 3 -t 100s'))
            self.workload_listing.append(WorkloadRecord('stress-io4-100s', 'stress','-i 4 -t 100s'))
            # ### ------------  CPU & IO Only workloads ------------ 
            # self.workload_listing.append(WorkloadRecord('stress-cpu_io1-100s', 'stress','-c 1 -i 1 -t 100s'))
            # self.workload_listing.append(WorkloadRecord('stress-cpu_io2-100s', 'stress','-c 2 -i 2 -t 100s'))
            # self.workload_listing.append(WorkloadRecord('stress-cpu_io3-100s', 'stress','-c 3 -i 3 -t 100s'))
            # self.workload_listing.append(WorkloadRecord('stress-cpu_io4-100s', 'stress','-c 4 -i 4 -t 100s'))
        ###################### Stress workloads - END   ######################

        #################### Compression Workloads - BEGIN   ####################
        if (self.enable_compress_workloads == True):
            self.workload_listing.append(WorkloadRecord('bzip2-webster','bzip2','-k -f webster'))
            self.workload_listing.append(WorkloadRecord('bzip2-enwik8','bzip2','-k -f enwik8'))
            self.workload_listing.append(WorkloadRecord('gzip-webster','gzip','-k -f webster'))
            self.workload_listing.append(WorkloadRecord('gzip-enwik8','gzip','-k -f enwik8'))
            # self.workload_listing.append(WorkloadRecord('xz-webster','xz','-k -f webster'))
            # self.workload_listing.append(WorkloadRecord('xz-enwik8','xz','-k -f enwik8'))
        #################### Compression Workloads - END     ####################

        ############## FFMPEG Encode/Decode Workloads - BEGIN   ##################
        if (self.enable_encode_workloads == True):
            self.workload_listing.append(WorkloadRecord('ffmpeg-360p','ffmpeg',
                        '-hide_banner -loglevel warning -i \'Silent Love-360p.mp4\' -y -c:v libx264 -crf 18 -preset veryslow -c:a copy out.mp4'))
            # self.workload_listing.append(WorkloadRecord('ffmpeg-720p','ffmpeg',
            #             '-hide_banner -loglevel warning -i \'Silent Love-720p.mp4\' -y -c:v libx264 -crf 18 -preset veryslow -c:a copy out.mp4'))
        ############## FFMPEG Encode/Decode Workloads - END     ##################
```

**Note:** 11-11-2023_20-21-43_BigCore-10itr-100msPerf-CPUFreq-2.0GHz.tar.bz2 is  gathered with full set of workloads. For remaining files, minimal set is gathered considering time-constraint.

