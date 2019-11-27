"""
=========================================================================
directed_rand_sim.py
=========================================================================
Script to run test cases on manually injected bugs

Author : Eric Tang (et396)
Date   : 25 November 2019
"""

#! /usr/bin/env python
import os
import time
import json
import sys
import random
import matplotlib.pyplot as plt
import argparse
from matplotlib import colors
from matplotlib.ticker import PercentFormatter

#-------------------------------------------------------------------------
# Helper functions and classes
#-------------------------------------------------------------------------

"""
From build directory, run:
python ../scripts/rand_sim.py              : runs the current design
python ../scripts/rand_sim.py --plot       : NO SIM; plot only
python ../scripts/rand_sim.py --bug-inject : Peitian's bug injector

--trials : number of trials
--simulations: each sim will have a new bug if --bug-inject enabled
"""


def parse_cmdline():
  p = argparse.ArgumentParser()
  # p.add_argument( "--input-spec" )
  p.add_argument( "--trials", action = "store", default = 1)
  p.add_argument( "--simulations", action = "store", default = 1 )
  p.add_argument( "--plot", action = 'store_true', default = False )
  p.add_argument( "--bug-inject",   action = 'store_true', default = False )
  # p.add_argument( "--functional",   action = 'store_true', default = False )

  opts = p.parse_args()
  return opts


def run_random(name, out_dir, test_num):
  '''
  Run completely random tests on cache design. 
  Records the total number of tests run, number of transactions in the failing test
  and the cache size in a json file

  :param name:
  :param out_dir:
  :param test_num: int, test number
  '''

  rpt_target = f"{out_dir}/{name}_N{test_num:03d}.json"
  print(f"RUNNING Complete Random test {test_num}")
  command = f"pytest --disable-pytest-warnings \
    ../BlockingCache/test/BlockingCacheRandomRTL_test.py -q\
    --rand-out-dir {rpt_target}"
  os.system(command)

def run_iter_deep(name, out_dir, test_num):
  '''
  Run iterative deepening test

  :param name: bug name
  :param out_dir: where to save the test
  :param test_num: test number
  '''
  
  rpt_target = f"{out_dir}/{name}_N{test_num:03d}.json"
  print(f"RUNNING Iterative Deepening test {test_num}")
  command = f"pytest --disable-pytest-warnings \
    ../BlockingCache/test/BlockingCache_iterdeepen_test.py -q\
    --rand-out-dir {rpt_target}"
  os.system(command)

if __name__ =="__main__":
  opts = parse_cmdline()

  sim_dir = 'directed_bugs_results_more'
  if not os.path.exists(sim_dir):
    os.mkdir( sim_dir )

  for j in range(int(opts.trials)):
    run_random('dirty_bit_bug', sim_dir, j)
    run_iter_deep('iter_dirty_bit_bug', sim_dir, j)
  
