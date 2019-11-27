import json
import numpy as np
import matplotlib.pyplot as plt
import os

titlefont = {'fontname':'Times New Roman', 'size': 40}
ylabelfont = {'fontname':'Times New Roman','size': 30}
xlabelfont = {'fontname':'Times New Roman','size': 20}


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

  rand_cacheSize = np.zeros((len(bugs), num_tests)) + 1
  iter_cacheSize = np.zeros((len(bugs), num_tests)) + 1
  hypothesis_cacheSize = np.zeros((len(bugs), num_tests)) + 1

  rand_clw = np.zeros((len(bugs), num_tests)) + 1
  iter_clw = np.zeros((len(bugs), num_tests)) + 1
  hypothesis_clw = np.zeros((len(bugs), num_tests)) + 1

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
      if onlyfiles[j].startswith('rand'):
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
  rand_cacheSize  = rand_cacheSize.transpose()
  rand_clw        = rand_clw.transpose()
  rand_trans      = rand_trans.transpose()
  rand_complexity = rand_complexity.transpose()

  iter_test       = iter_test.transpose()
  iter_cacheSize  = iter_cacheSize.transpose()
  iter_clw        = iter_clw.transpose()
  iter_trans      = iter_trans.transpose()
  iter_complexity = iter_complexity.transpose()

  hypothesis_test       = hypothesis_test.transpose()
  hypothesis_cacheSize  = hypothesis_cacheSize.transpose()
  hypothesis_clw        = hypothesis_clw.transpose()
  hypothesis_trans      = hypothesis_trans.transpose()
  hypothesis_complexity = hypothesis_complexity.transpose()


  # Plot Results
  fig, axs = plt.subplots(nrows=5, ncols=3, figsize=(20,35), sharey='row')

  axs[0, 0].boxplot(rand_test)
  axs[1, 0].boxplot(np.log2(rand_cacheSize))
  axs[2, 0].boxplot(np.log2(rand_clw))
  axs[3, 0].boxplot(rand_trans)
  axs[4, 0].boxplot(rand_complexity)

  axs[0, 1].boxplot(iter_test)
  axs[1, 1].boxplot(np.log2(iter_cacheSize))
  axs[2, 1].boxplot(np.log2(iter_clw))
  axs[3, 1].boxplot(iter_trans)
  axs[4, 1].boxplot(iter_complexity)

  axs[0, 2].boxplot(hypothesis_test)
  axs[1, 2].boxplot(np.log2(hypothesis_cacheSize))
  axs[2, 2].boxplot(np.log2(hypothesis_clw))
  axs[3, 2].boxplot(hypothesis_trans)
  axs[4, 2].boxplot(hypothesis_complexity)

  # Set Titles
  axs[0, 0].set_title('Complete Random',     **titlefont)
  axs[0, 1].set_title('Iterative Deepening', **titlefont)
  axs[0, 2].set_title('Hypothesis',          **titlefont)

  # Set y labels
  axs[0, 0].set_ylabel('Num tests',       **ylabelfont)
  axs[1, 0].set_ylabel('Num Cachelines',  **ylabelfont)
  axs[2, 0].set_ylabel('Cahceline Width', **ylabelfont)
  axs[3, 0].set_ylabel('Num Trans',       **ylabelfont)
  axs[4, 0].set_ylabel('Avg Complexity',  **ylabelfont)

  for r in range(5):
    for c in range(3):
      axs[r, c].spines['top'  ].set_visible( False )
      axs[r, c].spines['right'].set_visible( False )
      axs[r, c].set_xticklabels([])

  # Set x labels
  for i in range(3):
    axs[4, i].set_xticklabels(bugs, rotation=45, **xlabelfont)
  
  axs[4, i].set_xlabel('Bug Type', **ylabelfont)
 
  fig.savefig(os.path.join(results_dir,'directed_bug_results.pdf'), bbox_inches='tight')

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