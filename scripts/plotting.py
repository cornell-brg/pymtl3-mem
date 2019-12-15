import json
import numpy as np
import matplotlib.pyplot as plt
import os

titlefont = {'fontname':'Times New Roman', 'size': 40}
ylabelfont = {'fontname':'Times New Roman','size': 10}
xlabelfont = {'fontname':'Times New Roman','size': 10}


def plot(bugs, num_tests):
  '''
  Plots all directed bugs

  :param bugs: list of all bugs
  :param num_tests: number of tests run
  '''

  print("PLOTING")

  rand_test = np.zeros((len(bugs), num_tests)) - 1
  iter_test = np.zeros((len(bugs), num_tests)) - 1
  hypothesis_test = np.zeros((len(bugs), num_tests)) - 1

  rand_cacheSize = np.zeros((len(bugs), num_tests)) - 1
  iter_cacheSize = np.zeros((len(bugs), num_tests)) - 1
  hypothesis_cacheSize = np.zeros((len(bugs), num_tests)) - 1

  rand_clw = np.zeros((len(bugs), num_tests)) - 1
  iter_clw = np.zeros((len(bugs), num_tests)) - 1
  hypothesis_clw = np.zeros((len(bugs), num_tests)) - 1

  rand_trans = np.zeros((len(bugs), num_tests)) - 1
  iter_trans = np.zeros((len(bugs), num_tests)) - 1
  hypothesis_trans = np.zeros((len(bugs), num_tests)) - 1

  rand_complexity = np.zeros((len(bugs), num_tests)) - 1
  iter_complexity = np.zeros((len(bugs), num_tests)) - 1
  hypothesis_complexity = np.zeros((len(bugs), num_tests)) - 1

  results_dir = os.path.join(os.getcwd(), '..', 'results')

  # Parse data from json
  for i in range(len(bugs)):
    bug_dir = os.path.join(results_dir, bugs[i])
    onlyfiles = [f for f in os.listdir(bug_dir) if os.path.isfile(os.path.join(bug_dir, f))]

    for j in range(len(onlyfiles)):
      if onlyfiles[j].startswith('rand') or onlyfiles[j].startswith('complete_random'):
        filename = os.path.join(bug_dir, onlyfiles[j])
        with open(filename, 'r') as fd2:
          num = int(filename[-8:-5])
          try:
            stats = json.load(fd2)
            rand_test      [i, num] = stats['test']
            rand_cacheSize [i, num] = stats['cacheSize']/stats['clw']
            rand_clw       [i, num] = stats['clw']
            rand_trans     [i, num] = stats['trans']
            if 'testComplexity' in stats:
              rand_complexity[i, num] = stats['testComplexity']
          except:
            pass

    for j in range(len(onlyfiles)):
      if onlyfiles[j].startswith('iter'):
        filename = os.path.join(bug_dir, onlyfiles[j])
        with open(filename, 'r') as fd2:
          num = int(filename[-8:-5])
          try:
            stats = json.load(fd2)
            iter_test      [i, num] = stats['test']
            iter_cacheSize [i, num] = stats['cacheSize']/stats['clw']
            iter_clw       [i, num] = stats['clw']
            iter_trans     [i, num] = stats['trans']
            if 'testComplexity' in stats:
              iter_complexity[i, num] = stats['testComplexity']
          except:
            pass

    for j in range(len(onlyfiles)):
      if onlyfiles[j].startswith('hypothesis'):
        filename = os.path.join(bug_dir, onlyfiles[j])
        with open(filename, 'r') as fd2:
          num = int(filename[-8:-5])
          try:
            stats = json.load(fd2)
            hypothesis_test      [i, num] = stats['test']
            hypothesis_cacheSize [i, num] = stats['cacheSize']/stats['clw']
            hypothesis_clw       [i, num] = stats['clw']
            hypothesis_trans     [i, num] = stats['trans']
            if 'testComplexity' in stats:
              hypothesis_complexity[i, num] = stats['testComplexity']
          except:
            pass

  rand_test       = rand_test.transpose()
  rand_test       = filter_data(rand_test)
  rand_cacheSize  = rand_cacheSize.transpose()
  rand_cacheSize  = filter_data(rand_cacheSize)
  rand_clw        = rand_clw.transpose()
  rand_clw        = filter_data(rand_clw)
  rand_trans      = rand_trans.transpose()
  rand_trans      = filter_data(rand_trans)
  rand_complexity = rand_complexity.transpose()
  rand_complexity = filter_data(rand_complexity)

  iter_test       = iter_test.transpose()
  iter_test       = filter_data(iter_test)
  iter_cacheSize  = iter_cacheSize.transpose()
  iter_cacheSize  = filter_data(iter_cacheSize)
  iter_clw        = iter_clw.transpose()
  iter_clw        = filter_data(iter_clw)
  iter_trans      = iter_trans.transpose()
  iter_trans      = filter_data(iter_trans)
  iter_complexity = iter_complexity.transpose()
  iter_complexity = filter_data(iter_complexity)

  hypothesis_test       = hypothesis_test.transpose()
  hypothesis_test       = filter_data(hypothesis_test)
  hypothesis_cacheSize  = hypothesis_cacheSize.transpose()
  hypothesis_cacheSize  = filter_data(hypothesis_cacheSize)
  hypothesis_clw        = hypothesis_clw.transpose()
  hypothesis_clw        = filter_data(hypothesis_clw)
  hypothesis_trans      = hypothesis_trans.transpose()
  hypothesis_trans      = filter_data(hypothesis_trans)
  hypothesis_complexity = hypothesis_complexity.transpose()
  hypothesis_complexity = filter_data(hypothesis_complexity)

  # Plot Results
  fig, axs = plt.subplots(nrows=5, ncols=3, figsize=(6,8))

  axs[0, 0].boxplot(rand_test)
  axs[1, 0].boxplot(rand_cacheSize)
  axs[2, 0].boxplot(rand_clw)
  axs[3, 0].boxplot(rand_trans)
  axs[4, 0].boxplot(rand_complexity)

  axs[0, 1].boxplot(iter_test)
  axs[1, 1].boxplot(iter_cacheSize)
  axs[2, 1].boxplot(iter_clw)
  axs[3, 1].boxplot(iter_trans)
  axs[4, 1].boxplot(iter_complexity)

  axs[0, 2].boxplot(hypothesis_test)
  axs[1, 2].boxplot(hypothesis_cacheSize)
  axs[2, 2].boxplot(hypothesis_clw)
  axs[3, 2].boxplot(hypothesis_trans)
  axs[4, 2].boxplot(hypothesis_complexity)

  # Set y labels
  axs[0, 0].set_ylabel('# tests',       **ylabelfont)
  axs[1, 0].set_ylabel('# cache lines',  **ylabelfont)
  axs[2, 0].set_ylabel('cache line width (bits)', **ylabelfont)
  axs[3, 0].set_ylabel('# transactions',       **ylabelfont)
  axs[4, 0].set_ylabel('avg. complexity',  **ylabelfont)

  for r in [1,2,4]:
    for c in range(3):
      axs[r][c].set_yscale('log', basey=2)

  for r in range(5):
    for c in range(3):
      axs[r, c].spines['top'  ].set_visible( False )
      axs[r, c].spines['right'].set_visible( False )
      axs[r, c].set_xticklabels([])
      axs[r, c].get_yaxis().set_label_coords(-0.28,0.5)

  # Set x labels
  for i in range(3):
    axs[4, i].set_xticklabels(bugs, rotation=90, **xlabelfont)

  # axs[4, 0].set_xlabel('(a) CRT', **ylabelfont)
  # axs[4, 1].set_xlabel('(b) IDT', **ylabelfont)
  # axs[4, 2].set_xlabel('(c) PyH2', **ylabelfont)

  top_limit = [
    [80, 600, 80],
    [64, 64, 64],
    [1024, 1024, 1024],
    [100, 100, 4],
    [3*10**9, 3*10**9, 3*10**9],
  ]

  import math
  for r_idx in [0,3]:
    for c_idx in range(3):
      axs[r_idx][c_idx].set_ylim( bottom=0, top=top_limit[r_idx][c_idx]*1.2 )
      axs[r_idx][c_idx].set_yticks( range(0, math.ceil(top_limit[r_idx][c_idx]*1.2), top_limit[r_idx][c_idx]//2) )

  # Cachelines: r_idx = 1
  r_idx = 1
  for c_idx in range(3):
    axs[r_idx][c_idx].set_ylim( top=top_limit[r_idx][c_idx]*1.2 )
    axs[r_idx][c_idx].set_yticks( [ 2**x for x in range(12) if 2**x < top_limit[r_idx][c_idx]] )

  # cacheline width
  r_idx = 2
  for c_idx in range(3):
    axs[r_idx][c_idx].set_ylim( bottom=31, top=top_limit[r_idx][c_idx]*1.2 )
    axs[r_idx][c_idx].set_yticks( [ 2**x for x in range(12) if 31 < 2**x < top_limit[r_idx][c_idx]] )

  fig.savefig(os.path.join(results_dir,'directed_bug_results.pdf'), bbox_inches='tight')


def filter_data(data):
  '''
  :param data: 2d array that is filtered by column
  '''

  filter_data = []

  r, c = data.shape
  for i in range(c):
    col = data[:,i]
    fil_col = col[col > 0]
    filter_data.append(fil_col)

  return filter_data


if __name__ == '__main__':
    cwd = os.getcwd()
    results_dir = os.path.join(cwd, '..', 'results')
    # plot_boxplot(data_dir)
    bugs = os.listdir(results_dir)
    bugs_dir = []
    for b in bugs:
      if os.path.isdir(os.path.join(results_dir, b)):
        if b == 'random':
          bugs_dir.append(b)
        else:
          bugs_dir.insert(0,b)

    print(bugs_dir)
    plot(bugs_dir, 250)
