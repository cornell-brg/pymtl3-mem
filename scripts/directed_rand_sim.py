"""
=========================================================================
directed_rand_sim.py
=========================================================================
Script to run test cases on manually injected bugs
From build directory, run:
python ../scripts/rand_sim.py 
--trials : number of trials

Author : Eric Tang (et396)
Date   : 25 November 2019
"""

#! /usr/bin/env python
import argparse
import json
import os


def parse_cmdline():
  p = argparse.ArgumentParser()
  p.add_argument( "--trials", action = "store", default = 1)
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

  rpt_target = f"{out_dir}/crt_{name}_N{test_num:03d}.json"
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
  
  rpt_target = f"{out_dir}/idt_{name}_N{test_num:03d}.json"
  print(f"RUNNING Iterative Deepening test {test_num}")
  command = f"pytest --disable-pytest-warnings \
    ../BlockingCache/test/BlockingCache_iterdeepen_test.py -q\
    --rand-out-dir {rpt_target}"
  os.system(command)

def run_hypothesis(name, out_dir, test_num):
  '''
  Run hypothesis test

  :param name: bug name
  :param out_dir: where to save the test
  :param test_num: test number
  '''
  
  rpt_target = f"{out_dir}/pyh2_{name}_N{test_num:03d}.json"
  print(f"RUNNING hypothesis test {test_num}")
  command = f"pytest --disable-pytest-warnings \
    ../BlockingCache/test/BlockingCache_hypothesis_test.py -q\
    --rand-out-dir {rpt_target}"
  os.system(command)

if __name__ =="__main__":
  opts = parse_cmdline()
  bug_type = 'wr_hit'

  # results_dir = os.path.join(os.getcwd(),  bug_type)
  results_dir_crt  = os.path.join(os.getcwd(), '..', 'results', bug_type, 'CRT')
  results_dir_idt  = os.path.join(os.getcwd(), '..', 'results', bug_type, 'IDT')
  results_dir_pyh2 = os.path.join(os.getcwd(), '..', 'results', bug_type, 'PyH2')
  results_dir = [results_dir_pyh2]
  for folder in results_dir:
    if not os.path.exists(folder):
      os.mkdir( folder )

  for j in range(int(opts.trials)):
    # run_random(bug_type, results_dir_crt, j)
    # run_iter_deep(bug_type, results_dir_idt, j)
    run_hypothesis(bug_type, results_dir_pyh2, j)

    # Remove pytest and hypothesis cache
    os.system('rm -rf .hypothesis/')
    os.system('rm -rf .pytest/')
  
