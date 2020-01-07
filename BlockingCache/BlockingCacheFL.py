
"""
=========================================================================
 BlockingCacheFL.py
=========================================================================
A function level cache model which only passes cache requests and
responses to the memory

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   23 December 2019
"""

import math
import random

from pymtl3 import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

from mem_pclib.ifcs.ReqRespMsgTypes import ReqRespMsgTypes

# obw  = 8   # Short name for opaque bitwidth
# abw  = 32  # Short name for addr bitwidth
# dbw  = 32  # Short name for data bitwidth
# clw  = 128
# CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
# MemMsg = ReqRespMsgTypes(obw, abw, clw)

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( CacheMsg, type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheMsg.Req( type_, opaque, addr, len, data )

def resp( CacheMsg, type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheMsg.Resp( type_, opaque, test, len, data )

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
    self.nlines = int(size // linesize)
    self.nsets = int(self.nlines // self.nways)
    self.nbanks = nbanks

    # Compute how the address is sliced
    self.offset_start = 0
    self.offset_end = self.offset_start + int(math.log(linesize//8, 2))
    self.bank_start = self.offset_end
    if nbanks > 0:
      self.bank_end = self.bank_start + int(math.log(nbanks, 2))
    else:
      self.bank_end = self.bank_start
    self.idx_start = self.bank_end
    self.idx_end = self.idx_start + int(math.log(self.nsets, 2))
    self.tag_start = self.idx_end
    self.tag_end = 32

    # print(self.offset_start,self.bank_start,self.idx_start,self.tag_start)
    # Initialize the tag and valid array
    # Both arrays are of the form line[idx][way]
    # Note that line[idx] is a one-element array for
    # a direct-mapped cache
    self.line = []
    self.valid = []
    for n in range(self.nlines):
      self.line.insert(n, [Bits(32, 0) for x in range(nways)])
      self.valid.insert(n, [False for x in range(nways)])

    # Initialize the lru array
    # Implemented as an array for each set index
    # lru[idx][0] is the most recently used
    # lru[idx][-1] is the least recently used
    self.lru = []
    for n in range(self.nsets):
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
  def __init__(self, size, nways, nbanks, CacheMsg, MemMsg, mem=None):
    # The hit/miss tracker
    self.tracker = HitMissTracker(size, nways, nbanks, MemMsg.dbw)

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
    self.opaque = 0
    self.CacheMsg = CacheMsg
    self.MemMsg = MemMsg

  def check_hit(self, addr):
    # Tracker returns boolean, need to convert to 1 or 0 to use
    # in the "test" field of the response
    if self.tracker.access_address(addr):
      return 1
    else:
      return 0

  def read(self, addr, opaque, len_):
    hit = self.check_hit(addr)

    if addr.int() in self.mem:
      value = self.mem[addr.int()]
    else:
      value = Bits(32, 0)

    # opaque = random.randint(0,255)
    self.transactions.append(req(self.CacheMsg,'rd', opaque, addr, len_, 0))
    self.transactions.append(resp(self.CacheMsg,'rd', opaque, hit, len_, value))
    self.opaque += 1

  def write(self, addr, value, opaque, len_):
    value = Bits(32, value)
    hit = self.check_hit(addr)

    self.mem[addr.int()] = value

    # opaque = random.randint(0,255)
    self.transactions.append(req(self.CacheMsg,'wr', opaque, addr, len_, value))
    self.transactions.append(resp(self.CacheMsg,'wr', opaque, hit, len_, 0))
    self.opaque += 1
  
  def init(self, addr, value, opaque, len_):
    value = Bits(32, value)
    hit = self.check_hit(addr)
    if len_ == 1:
      self.mem[addr.int()] == self.mem[addr.int()][]
    else:
      self.mem[addr.int()] = value

    self.transactions.append(req(self.CacheMsg,'in', opaque, addr, len_, value))
    self.transactions.append(resp(self.CacheMsg,'in', opaque, 0, len_, 0))
    self.opaque += 1

  def get_transactions(self):
    return self.transactions
