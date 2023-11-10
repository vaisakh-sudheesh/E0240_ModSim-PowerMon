#!/usr/bin/env python3
import tqdm
import time

def sleep_progress(timeout_s:int ) -> None:
    sleep1_pbar = tqdm.tqdm(range(timeout_s), bar_format='{desc} {percentage:3.0f}%|{bar}|{remaining} seconds')
    sleep1_pbar.set_description("Waiting")
    for i in sleep1_pbar:
        time.sleep(1)