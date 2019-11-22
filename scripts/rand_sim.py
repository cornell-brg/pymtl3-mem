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

def parse_cmdline():
  p = argparse.ArgumentParser()
  # p.add_argument( "--input-spec" )
  p.add_argument( "--trials" )
  p.add_argument( "--simulations" )
  p.add_argument( "--plot", action = 'store_true', default = False )
  p.add_argument( "--bug-inject",   action = 'store_true', default = False )
  # p.add_argument( "--functional",   action = 'store_true', default = False )

  opts = p.parse_args()
  return opts

PATH_TO_CTRL = "../BlockingCache/BlockingCacheCtrlPRTL.py"
operators = {
  "random_bug" : {
    'trials'   : 3,
    'max_test' : 1,
  }  
}

def initial():
  
  os.system("cp {0} {0}_correct".format(PATH_TO_CTRL))
  command = "python {} --input-spec {} \
     --functional --no-astdump".format(
      "~/work/pymtl3/scripts/bug-injector/bug_injector.py",
      "mutation_targets.json"
  )
  os.system(command)

def finish():
  os.system("mv {0}_correct {0}".format(PATH_TO_CTRL))

def run(name, out_dir, test_num):
  rpt_target = "{}/{}_N{:03d}.json".format(\
    out_dir, name, test_num )
  os.system("echo -e '\033[{};3{}m'RUNNING'\033[0m' \
    test={} rpt_dir={} test_num={}".format(\
    random.randint(0,1), random.randint(0,7), name,rpt_target,test_num))
  command = "pytest --disable-pytest-warnings \
    ../BlockingCache/test/BlockingCacheRandomRTL_test.py\
    -k test_bug_inj -q --rand-out-dir {}".format(rpt_target)
  os.system(command)
  # print(command)

def plot(out_dir):
  print("PLOTING")
  onlyfiles = [f for f in os.listdir(out_dir) \
    if os.path.isfile(os.path.join(out_dir, f))]
  test_vector = []
  transaction_vector = []
  for i in range(len(onlyfiles)):
    with open("{}/{}".format(out_dir,onlyfiles[i]), 'r') as fd2:
      stats = json.load(fd2)
      test_vector.append(stats['test'])
      transaction_vector.append(stats['trans'])
  plt.hist(test_vector, density=False, bins=auto)
  plt.title('Histogram for Number of Tests')
  plt.xlabel('Tests')  
  plt.ylabel('Bugs')  
  plt.savefig('Tests.pdf')
  plt.hist(transaction_vector, density=False, bins=auto)
  plt.title('Histogram for Number of Transactions')
  plt.xlabel('Number of Transactions')  
  plt.ylabel('Bugs')  
  plt.savefig('Transactions.pdf')

  plt.hist2d(test_vector, transaction_vector, bins=auto, density=False, cmap='plasma')
  plt.title('Heat Map for Number of Transactions')
  plt.xlabel('Tests')  
  plt.ylabel('Transactions')  
  cb = plt.colorbar()
  cb.set_label('Number of Bugs')
  plt.savefig('HeatMap.pdf')



if __name__ =="__main__":
  os.system("cd .. && cd build")
  for op, d in operators.items():
    # print (op, d)
    opts = parse_cmdline()
    
    sim_dir = "{}_logs".format(op)
    if opts.plot:
      plot(sim_dir)
    else:
      # if not os.path.exists( sim_dir ):
      max_test = d['max_test']
      trials = d['trials']
      os.system("rm -rf {}".format(sim_dir))
      os.mkdir( sim_dir )
      for j in range( max_test):
        if opts.bug_inject:
          initial()
        for i in range( trials ):
          run(op, sim_dir, i+trials*j)
        if opts.bug_inject:
          finish()
      plot(sim_dir)


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