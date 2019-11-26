import json
import matplotlib.pyplot as plt
import os

def plot(out_dir):

  print("PLOTING")

  # Parse data from json
  onlyfiles = [f for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))]
  test_vector = []
  transaction_vector = []
  cacheSize_vector = []
  clw_vector = []
  for i in range(len(onlyfiles)):
    with open("{}/{}".format(out_dir,onlyfiles[i]), 'r') as fd2:
      stats = json.load(fd2)
      test_vector.append(stats['test'])
      transaction_vector.append(stats['trans'])
      if stats['failed']:
        cacheSize_vector.append(stats['cacheSize'])
        clw_vector.append(stats['clw'])


  i = 0
  while i < len(test_vector):
    if test_vector[i] >= 1000:
      del(test_vector[i])
    else:
      i += 1
  print(test_vector)


  # Plot Results
  fig, (ax1,ax2,ax3,ax4) = plt.subplots(nrows=1, ncols=4, sharey='row')
  
  ax1.hist(test_vector, density=False, bins=30)
  ax1.set_xlabel('Tests',fontsize = 10) 
  ax1.set_ylabel('Frequency',fontsize = 10) 

  ax2.hist(transaction_vector, density=False, bins=30)
  ax2.set_xlabel('Transactions',fontsize = 10) 

  ax3.hist(cacheSize_vector, density=False, bins=30)
  ax3.set_xlabel('Cache Size',fontsize = 10) 
  ax3.tick_params(axis='both', which='major', labelsize=8)

  ax4.hist(clw_vector, density=False, bins=30)
  ax4.set_xlabel('Cacheline Size',fontsize = 10) 
  
  fig.savefig(f'{out_dir}_sim_plots.pdf')

def plot_boxplot(out_dir):
  print("PLOTING")

  # Parse data from json
  onlyfiles = [f for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))]
  test_vector = []
  transaction_vector = []
  cacheSize_vector = []
  clw_vector = []
  for i in range(len(onlyfiles)):
    with open("{}/{}".format(out_dir,onlyfiles[i]), 'r') as fd2:
      stats = json.load(fd2)
      test_vector.append(stats['test'])
      transaction_vector.append(stats['trans'])
      if stats['failed']:
        cacheSize_vector.append(stats['cacheSize'])
        clw_vector.append(stats['clw'])


  i = 0
  while i < len(test_vector):
    if test_vector[i] >= 1000:
      del(test_vector[i])
    else:
      i += 1
  print(test_vector)


  # Plot Results
  fig, (ax1,ax2,ax3,ax4) = plt.subplots(nrows=1, ncols=4)
  
  ax1.boxplot(test_vector)
  ax1.set_xlabel('Tests',fontsize = 10) 
  ax1.set_ylabel('Frequency',fontsize = 10) 

  ax2.boxplot(transaction_vector)
  ax2.set_xlabel('Transactions',fontsize = 10) 

  ax3.boxplot(cacheSize_vector)
  ax3.set_xlabel('Cache Size',fontsize = 10) 
  ax3.tick_params(axis='both', which='major', labelsize=8)

  ax4.boxplot(clw_vector)
  ax4.set_xlabel('Cacheline Size',fontsize = 10) 
  
  fig.savefig(f'{out_dir}_sim_plots.pdf')  

if __name__ == '__main__':
    cwd = os.getcwd()
    data_dir = os.path.join(cwd,'directed_bugs_results')
    plot_boxplot(data_dir)