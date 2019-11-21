'''
===============================================================================
ModelCache.py
===============================================================================
Golden cache model

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   20 November 2019
'''

#----------------------------------------------------------------------
# Enhanced random tests
#----------------------------------------------------------------------
# This set of random tests uses a cache model that properly tracks
# hits and misses, and should completely accurately model eviction
# behavior. The model is split up into a hit/miss tracker, and a
# transaction generator, so that the hit/miss tracker can be reused
# in an FL model

class HitMissTracker:
  def __init__(self, size, nways, nbanks, linesize):
    # Compute various sizes
    self.nways = nways
    self.linesize = linesize
    self.nlines = int(size / linesize)
    self.nsets = int(self.nlines / self.nways)
    self.nbanks = nbanks

    # Compute how the address is sliced
    self.offset_start = 0
    self.offset_end = self.offset_start + int(math.log(linesize, 2))
    self.bank_start = self.offset_end
    if nbanks > 0:
      self.bank_end = self.bank_start + int(math.log(nbanks, 2))
    else:
      self.bank_end = self.bank_start
    self.idx_start = self.bank_end
    self.idx_end = self.idx_start + int(math.log(self.nsets, 2))
    self.tag_start = self.idx_end
    self.tag_end = 32

    # Initialize the tag and valid array
    # Both arrays are of the form line[idx][way]
    # Note that line[idx] is a one-element array for
    # a direct-mapped cache
    self.line = []
    self.valid = []
    for n in xrange(self.nlines):
      self.line.insert(n, [Bits(32, 0) for x in xrange(nways)])
      self.valid.insert(n, [False for x in xrange(nways)])

    # Initialize the lru array
    # Implemented as an array for each set index
    # lru[idx][0] is the most recently used
    # lru[idx][-1] is the least recently used
    self.lru = []
    for n in xrange(self.nsets):
      self.lru.insert(n, [x for x in range(nways)])

  # Generate the components of an address
  # Ignores the bank bits, since they don't affect the behavior
  # (and may not even exist)
  def split_address(self, addr):
    addr = Bits(32, addr)
    offset = addr[self.offset_start:self.offset_end]
    idx = addr[self.idx_start:self.idx_end]
    tag = addr[self.tag_start:self.tag_end]
    return (tag, idx, offset)

  # Update the LRU status, given that a hit just occurred
  def lru_hit(self, idx, way):
    self.lru[idx].remove(way)
    self.lru[idx].insert(0, way)

  # Get the least recently used way for an index
  # The LRU is always the last element in the list
  def lru_get(self, idx):
    return self.lru[idx][-1]

  # Perform a tag check, and update lru if a hit occurs
  def tag_check(self, tag, idx):
    for way in range(self.nways):
      if self.valid[idx][way] and self.line[idx][way] == tag:
        # Whenever tag check hits, update the set's lru array
        self.lru_hit(idx, way)
        return True
    return False

  # Update the tag array due to a value getting fetched from memory
  def refill(self, tag, idx):
    victim = self.lru_get(idx)
    self.line[idx][victim] = tag
    self.valid[idx][victim] = True
    self.lru_hit(idx, victim)

  # Simulate accessing an address. Returns True if a hit occurred,
  # False on miss
  def access_address(self, addr):
    (tag, idx, offset) = self.split_address(addr)
    hit = self.tag_check(tag, idx)
    if not hit:
      self.refill(tag, idx)

    return hit

class ModelCache:
  def __init__(self, size, nways, nbanks, linesize, mem=None):
    # The hit/miss tracker
    self.tracker = HitMissTracker(size, nways, nbanks, linesize)

    self.mem = {}

    # Unpack any initial values of memory into a dict (has easier lookup)
    #
    # zip is used here to convert the mem array into an array of
    # (addr, value) pairs (which it really should be in the first
    # place)
    if mem:
      for addr, value in zip(mem[::2], mem[1::2]):
        self.mem[addr] = Bits(32, value)

    # The transactions list contains the requests and responses for
    # the stream of read/write calls on this model
    self.transactions = []

  def check_hit(self, addr):
    # Tracker returns boolean, need to convert to 1 or 0 to use
    # in the "test" field of the response
    if self.tracker.access_address(addr):
      return 1
    else:
      return 0

  def read(self, addr):
    hit = self.check_hit(addr)

    if addr.int() in self.mem:
      value = self.mem[addr.int()]
    else:
      value = Bits(32, 0)

    opaque = random.randint(0,255)
    self.transactions.append(req('rd', opaque, addr, 0, 0))
    self.transactions.append(resp('rd', opaque, hit, 0, value))

  def write(self, addr, value):
    value = Bits(32, value)
    hit = self.check_hit(addr)

    self.mem[addr.int()] = value

    opaque = random.randint(0,255)
    self.transactions.append(req('wr', opaque, addr, 0, value))
    self.transactions.append(resp('wr', opaque, hit, 0, 0))
    
  def get_transactions(self):
    return self.transactions

