"""
=========================================================================
rand_sim.py
=========================================================================
Script to run test cases

Author : Xiaoyu Yan, Eric Tang (et396)
Date   : 22 November 2019
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
tag = 9
#-------------------------------------------------------------------------
# Helper functions and classes
#-------------------------------------------------------------------------

"""
From build directory, run:
python ../scripts/rand_sim.py              : runs the current design
python ../scripts/rand_sim.py --plot       : NO SIM; plot only
python ../scripts/rand_sim.py --bug-inject : Peitian's bug injector

--trials : number of times we run the simulation with the same bug
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

PATH_TO_CTRL = "../BlockingCache/BlockingCacheCtrlPRTL.py"
operators = {
  "complete_random" : {
    'test_to_run': "BlockingCacheRandomRTL_test",
  },  
  "iterative_deepen" : {
    'test_to_run': "BlockingCache_iterdeepen_test",
  },
  "hypothesis" : {
    'test_to_run': "BlockingCache_hypothesis_test",
  }
}

def initial(sim_num):
  
  flags = ["--functional", "--if-const", "--expr-elim"]
  os.system("cp {0} {0}_correct".format(PATH_TO_CTRL))
  command = "echo sim_num = {} >>inject_{}.out 2>&1".format(sim_num,tag)
  os.system(command)
  command = "python {} --input-spec {} \
     {} --no-astdump >>inject_{}.out 2>&1".format(
      "~/work/pymtl3-mem/scripts/bug_injector.py",
      "mutation_targets.json",flags[random.randint(0,2)],tag 
  ) # Fix the flags!! 
  print(f"NEW BUG cmd={command}")
  os.system(command)

def finish():
  os.system("mv {0}_correct {0}".format(PATH_TO_CTRL))

def run(name, out_dir, test_num, test):
  rpt_target = "{}/{}_N{:03d}.json".format(\
    out_dir, name, test_num )
  os.system("echo -e '\033[{};3{}m'RUNNING'\033[0m' \
    test={} rpt_dir={} test_num={}".format(\
    random.randint(0,1), random.randint(0,7), name,rpt_target,test_num))
  command = "pytest --disable-pytest-warnings \
    ../BlockingCache/test/{}.py -q\
     --rand-out-dir {}".format(test, rpt_target)
  os.system(command)
  # print(command)

def plot(op,out_dir):
  print("PLOTING")
  onlyfiles = [f for f in os.listdir(out_dir) \
    if os.path.isfile(os.path.join(out_dir, f))]
  test_vector = []
  transaction_vector = []
  cacheSize_vector = []
  clw_vector = []
  for i in range(len(onlyfiles)):
    with open("{}/{}".format(out_dir,onlyfiles[i]), 'r') as fd2:
      stats = json.load(fd2)
      transaction_vector.append(stats['trans'])
      if op=="iterative_deepen":
        if stats['failed']:
          test_vector.append(stats['test'])
      else:
        test_vector.append(stats['test'])
      
      if stats['failed']:
        cacheSize_vector.append(stats['cacheSize'])
        clw_vector.append(stats['clw'])
  # print (test_vector)
  
  fig, (ax1,ax2,ax3,ax4) = plt.subplots(nrows=1, ncols=4, sharey='row')
  
  ax1.hist(test_vector, bins=100)#range=(0, max(test_vector)))
  ax1.set_xlabel('Tests',fontsize = 10) 
  ax1.set_ylabel('Number of Bugs',fontsize = 10) 

  ax2.hist(transaction_vector, bins=50)#range=(0, max(transaction_vector)))
  ax2.set_xlabel('Transactions',fontsize = 10) 

  ax3.hist(cacheSize_vector, bins=30)#range=(0, max(cacheSize_vector)))
  ax3.set_xlabel('Cache Size',fontsize = 10) 
  # ax3.tick_params(axis='both', which='major', labelsize=8)

  ax4.hist(clw_vector, bins=30)#range=(0, max(clw_vector)))
  ax4.set_xlabel('Cacheline Size',fontsize = 10) 
  
  fig.savefig(f'{out_dir}_sim_plots.pdf')

  # fig = plt.figure()
  # fig, (ax1,ax2,ax3,ax4) = plt.subplots(nrows=1, ncols=4, sharey='row')
  # h = ax1.hist2d(test_vector, transaction_vector, bins=30, density=False, cmap='plasma')
  # ax1.set_xlabel('Tests')  
  # ax1.set_ylabel('Transactions')  
  # cb = plt.colorbar(h[3], ax=ax1)
  # cb.set_label('Number of Bugs')
  # h = ax2.hist2d(cacheSize_vector, transaction_vector, bins=30, density=False, cmap='plasma')
  # ax2.set_xlabel('Cache Size')  
  # ax2.set_ylabel('Transactions')  
  # cb = plt.colorbar(h[3], ax=ax2)
  # cb.set_label('Number of Bugs')

  # plt.savefig('HeatMap.pdf')

if __name__ =="__main__":
  start = time.monotonic()
  os.system("cd .. && cd build")
  opts = parse_cmdline()
  # if opts.bug_inject:
  #   os.system("inject_{}.out".format(tag))
  if opts.plot:
    for op, d in operators.items():   
      sim_dir = "{}_{}_logs".format(op,tag)
      plot(op,sim_dir)
  else:
    for op, d in operators.items():   
      sim_dir = "{}_{}_logs".format(op,tag)
      if not os.path.exists( sim_dir ):
        # os.system("rm -rf {}".format(sim_dir))
        os.mkdir( sim_dir )
    for j in range(int(opts.simulations)):
      if opts.bug_inject:
        initial(j)
      for i in range(int(opts.trials)):
        for op, d in operators.items():   
          sim_dir = "{}_{}_logs".format(op,tag)
          test = d["test_to_run"]
          run(op, sim_dir, i+int(opts.trials)*j, test)
      if opts.bug_inject:
        finish()
    for op, d in operators.items():   
      sim_dir = "{}_{}_logs".format(op,tag)
      plot(op,sim_dir) 
  
  end = time.monotonic()
  print (end-start)
# def task_sim():
#   for op, d in operators.items():
#     # print (op, d)
#     max_test = d['max_test']
#     sim_dir = "{}_logs".format(op)
#     if not os.path.exists( sim_dir ):
#       os.mkdir( sim_dir )

#     action = (run, [op, sim_dir, max_test])
#     targets = [sim_dir]   

#     taskdict = {\
#       'basename' : 'sim',
#       # 'name'     : op,
#       'actions'  : [action],
#       'targets'  : targets,
#       'task_dep' : [],
#       'uptodate' : [True],
#       'clean'    : ['rm -rf ' + i for i in targets ],
#       'verbosity': 2   
#     }
#     yield taskdict