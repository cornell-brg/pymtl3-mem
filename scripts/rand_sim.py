#! /usr/bin/env python
import os
import time
import json
import sys
import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.ticker import PercentFormatter


operators = {
  "random_bug" : {
    'trials'   : 20,
    'max_test' : 20,
  }  
}

def initialization():
  PATH_TO_CTRL = "/home/xy97/"
  command = "python {} --input-spec {} \
    --no-overwrite --functional --no-astdump".format(
      "~/work/pymtl3/scripts/bug-injector/bug_injector.py",
      "mutation_targets.json"
  )
  os.system(command)

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
  print(command)

def plot(out_dir):
  onlyfiles = [f for f in os.listdir(out_dir) \
    if os.path.isfile(os.path.join(out_dir, f))]
  test_vector = []
  for i in range(len(onlyfiles)):
    with open("{}/{}".format(out_dir,onlyfiles[i]), 'r') as fd2:
      stats = json.load(fd2)
      test_vector.append(stats['test'])
  plt.hist(test_vector, density=False, bins=30)
  plt.xlabel('Tests')  
  plt.ylabel('Bugs')  
  plt.savefig('histogram.pdf')


if __name__ =="__main__":
  os.system("cd .. && cd build")
  for op, d in operators.items():
    # print (op, d)
    max_test = d['max_test']
    trials = d['trials']
    sim_dir = "{}_logs".format(op)
    if not os.path.exists( sim_dir ):
      os.mkdir( sim_dir )
    initialization()
    # for i in range( trials ):
    #   run(op, sim_dir, i)
    # plot(sim_dir)


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