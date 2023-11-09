# Results Dataset

## Top level 

| Results Directory Name        | Description/Notes                                                   |
| ----------------------------- | ------------------------------------------------------------------- |
| BigCore-Frequency-Stepping    | Seggregated test of individual workload types (compression, stress, video-encode). Each done from frequency ranges of 2.0GHz ~ 1.2GHz on Big/Performance cores |
| IdlePower-Frequency-Stepping  | Idle power consumption without any workload running, under two conditions of (1) both ethernet and UART connected, (2) With only UART connected. |
| Corewise-100ms-Sampling       | Samples of all(compression, stress, video-encode) workloads, for big and little cores performed separately.|
| Archived                      | Older test data as listed in table below

----------

### Archived directory
| Archived Directory Name       | Description/Notes                                                   |
| ----------------------------- | ------------------------------------------------------------------- |
| 10-30-2023_11-58-22     | Stress workload with CPU and IO  operations for a duration of 100seconds and 10 iterations each <ul><li>**stress-\<x\>-cpu**: CPU-only stress workload</li><li>**stress-\<x\>-io**: IO-only stress workload</li><li>**stress-\<x\>-cpuio**: CPU+IO stress workload</li></ul>|
| 10-31-2023_11-00-33     |  3 Iterations of each test: <ul><li>**stress-\<x\>**: Stress workload with CPU and IO  operations for a duration of 100seconds of CPU & IO stress load mix</li><li>**gzip\|bzip2\|xz-\<x\>**: Compression workloads of each algorithm</li><li>**ffmpeg-\<res\>-\<x\>**: FFMPEG encoding workloads of 320p and 720p videos</li></ul>|
