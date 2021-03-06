
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

from pymtl3 import *

from mem_ifcs.MemMsg import MemMsgType

# Assumes 32 bit address and 32 bit data

#-------------------------------------------------------------------------
# Make messages
#-------------------------------------------------------------------------

def req( CacheReqType, type_, opaque, addr, len, data ):
  # type_ as string
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  elif type_ == 'ad': type_ = MemMsgType.AMO_ADD
  elif type_ == 'an': type_ = MemMsgType.AMO_AND
  elif type_ == 'or': type_ = MemMsgType.AMO_OR
  elif type_ == 'sw': type_ = MemMsgType.AMO_SWAP
  elif type_ == 'mi': type_ = MemMsgType.AMO_MIN
  elif type_ == 'mu': type_ = MemMsgType.AMO_MINU
  elif type_ == 'mx': type_ = MemMsgType.AMO_MAX
  elif type_ == 'xu': type_ = MemMsgType.AMO_MAXU
  elif type_ == 'xo': type_ = MemMsgType.AMO_XOR
  elif type_ == 'inv': type_ = MemMsgType.INV
  elif type_ == 'fl':  type_ = MemMsgType.FLUSH
  return CacheReqType( type_, opaque, addr, len, data )

def resp( CacheRespType, type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  elif type_ == 'ad': type_ = MemMsgType.AMO_ADD
  elif type_ == 'an': type_ = MemMsgType.AMO_AND
  elif type_ == 'or': type_ = MemMsgType.AMO_OR
  elif type_ == 'sw': type_ = MemMsgType.AMO_SWAP
  elif type_ == 'mi': type_ = MemMsgType.AMO_MIN
  elif type_ == 'mu': type_ = MemMsgType.AMO_MINU
  elif type_ == 'mx': type_ = MemMsgType.AMO_MAX
  elif type_ == 'xu': type_ = MemMsgType.AMO_MAXU
  elif type_ == 'xo': type_ = MemMsgType.AMO_XOR
  elif type_ == 'inv': type_ = MemMsgType.INV
  elif type_ == 'fl':  type_ = MemMsgType.FLUSH
  return CacheRespType( type_, opaque, test, len, data )

#-------------------------------------------------------------------------
# Define AMO functions
#-------------------------------------------------------------------------

AMO_FUNS = { MemMsgType.AMO_ADD  : lambda m,a : m+a,
             MemMsgType.AMO_AND  : lambda m,a : m&a,
             MemMsgType.AMO_OR   : lambda m,a : m|a,
             MemMsgType.AMO_SWAP : lambda m,a : a,
             MemMsgType.AMO_MIN  : lambda m,a : m if m.int() < a.int() else a,
             MemMsgType.AMO_MINU : min,
             MemMsgType.AMO_MAX  : lambda m,a : m if m.int() > a.int() else a,
             MemMsgType.AMO_MAXU : max,
             MemMsgType.AMO_XOR  : lambda m,a : m^a,
           }

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

    # Initialize the tag and valid array
    # Both arrays are of the form line[idx][way]
    # Note that line[idx] is a one-element array for a direct-mapped cache
    self.line = []
    self.valid = []
    for n in range(self.nlines):
      self.line.insert(n, [Bits(32, 0) for x in range(nways)])
      self.valid.insert(n, [False for x in range(nways)])

    # Initialize the LRU array
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

  def lru_set(self, idx, way):
    self.lru[idx].remove(way)
    self.lru[idx].append(way)

  def amo_req(self, addr):
    (tag, idx, offset) = self.split_address(addr)
    for way in range(self.nways):
      if self.valid[idx][way] and self.line[idx][way] == tag:
        self.valid[idx][way] = False
        self.lru_set( idx, way )
        break
  
  def invalidate(self):
    # invalidates all the cachelines
    for way in range(self.nways):
      for idx in range(self.nsets):
        self.valid[idx][way] = False

class ModelCache:
  def __init__(self, size, nways, nbanks, CacheReqType, CacheRespType, MemReqType, MemRespType, mem=None):
    # The hit/miss tracker
    self.mem_bitwidth_data = MemReqType.get_field_type("data").nbits
    self.cache_bitwidth_data = CacheReqType.get_field_type("data").nbits
    self.BitsData = mk_bits(self.cache_bitwidth_data)
    size = size*8
    self.tracker = HitMissTracker(size, nways, nbanks, self.mem_bitwidth_data)
  
    # The transactions list contains the requests and responses for
    # the stream of read/write calls on this model
    self.transactions = []
    self.opaque = 0
    self.CacheReqType = CacheReqType
    self.CacheRespType = CacheRespType
    self.MemReqType = MemReqType
    self.MemRespType = MemRespType
    self.nlines = int(size // self.mem_bitwidth_data)
    self.nsets = int(self.nlines // nways)
    # Compute how the address is sliced
    self.offset_start = 0
    self.offset_end = self.offset_start + int(math.log(self.mem_bitwidth_data//8, 2))
    self.idx_start = self.offset_end
    self.idx_end = self.idx_start + int(math.log(self.nsets, 2))
    self.tag_start = self.idx_end
    self.tag_end = 32
    
    # Unpack any initial values of memory into a dict (has easier lookup)
    #
    # zip is used here to convert the mem array into an array of
    # (addr, value) pairs (which it really should be in the first
    # place)
    self.mem = {}
    if mem:
      for addr, value in zip(mem[::2], mem[1::2]):
        offset = int(Bits32(addr)[ self.offset_start : self.offset_end ])
        addr   = int(Bits32(addr)[ self.offset_end : 32 ])
        if addr not in self.mem:
          self.mem[addr] = Bits(self.mem_bitwidth_data, 0)
        # assume word mem declarations
        self.mem[addr][ offset*8 : (offset+4)*8 ] = value

  def check_hit(self, addr):
    # Tracker returns boolean, need to convert to 1 or 0 to use
    # in the "test" field of the response
    if self.tracker.access_address(addr):
      return 1
    else:
      return 0

  def read(self, addr, opaque, len_):
    hit = self.check_hit(addr)
    new_addr = int(addr[self.offset_end:32])
    offset = int(addr[self.offset_start:self.offset_end])
    if new_addr not in self.mem:
      self.mem[new_addr] = Bits(self.mem_bitwidth_data, 0)
    if len_ == 0:
      value = self.mem[new_addr][offset*8 : (offset+self.cache_bitwidth_data/8)*8]
    else:
      value = self.mem[new_addr][offset*8 : (offset + int(len_))*8 ]
    
    value = zext(value, self.cache_bitwidth_data)
    self.transactions.append(req (self.CacheReqType, 'rd', opaque, addr, len_, 0))
    self.transactions.append(resp(self.CacheRespType,'rd', opaque, hit,  len_, value))
    self.opaque += 1

  def write(self, addr, value, opaque, len_):
    hit = self.check_hit(addr)
    new_addr = int(addr[self.offset_end:32])
    offset = int(addr[self.offset_start:self.offset_end])
    value = Bits(self.cache_bitwidth_data, value)
    if new_addr not in self.mem:
      self.mem[new_addr] = Bits(self.mem_bitwidth_data, 0)
    if len_ == 0:
      self.mem[new_addr][offset*8 : (offset+self.cache_bitwidth_data/8)*8] = value[0 : self.cache_bitwidth_data ]
    else:
      self.mem[new_addr][offset*8 : (offset + int(len_))*8] = value[0 : int(len_)*8 ]

    self.transactions.append(req (self.CacheReqType, 'wr', opaque, addr, len_, value))
    self.transactions.append(resp(self.CacheRespType,'wr', opaque, hit,  len_, 0))
    self.opaque += 1

  def init(self, addr, value, opaque, len_):
    hit = self.check_hit(addr)
    new_addr = int(addr[self.offset_end:32])
    offset = int(addr[self.offset_start:self.offset_end])
    value = Bits(self.cache_bitwidth_data, value)
    if new_addr not in self.mem:
      self.mem[new_addr] = Bits(self.mem_bitwidth_data, 0)
    if len_ == 0:
      self.mem[new_addr][offset*8 : (offset+self.cache_bitwidth_data/8)*8] = value
    else:
      self.mem[new_addr][offset*8 : (offset + int(len_))*8 ] = value
    self.transactions.append(req(self.CacheReqType,'in', opaque, addr, len_, value))
    self.transactions.append(resp(self.CacheRespType,'in', opaque, 0, len_, 0))
    self.opaque += 1

  def amo(self, addr, value, opaque, len_, func):
    # AMO operations are on the word level only
    self.tracker.amo_req(addr)
    new_addr = addr[self.offset_end:32]
    offset = int(addr[self.offset_start:self.offset_end])
    if new_addr not in self.mem:
      self.mem[new_addr] = Bits(self.mem_bitwidth_data, 0)
    ret = self.mem[new_addr.int()][offset * 8 : (offset + 4) * 8]
    
    value = trunc(value, 32)
    amo_out = AMO_FUNS[ int(func) ]( ret, value )
    ret = zext( ret, self.cache_bitwidth_data )
    value = zext( value, self.cache_bitwidth_data )
    self.mem[new_addr.int()][offset * 8 : (offset + 4) * 8] = amo_out
    
    self.transactions.append(req (self.CacheReqType, func, opaque, addr, len_, value))
    self.transactions.append(resp(self.CacheRespType,func, opaque, 0,    len_, ret))
    self.opaque += 1

  def invalidate(self, opaque):
    self.tracker.invalidate()
    self.transactions.append(req (self.CacheReqType, 'inv', opaque, 0, 0, 0))
    self.transactions.append(resp(self.CacheRespType, 'inv', opaque, 0, 0, 0))
    self.opaque += 1

  def flush(self, opaque):
    self.transactions.append(req (self.CacheReqType, 'fl', opaque, 0, 0, 0))
    self.transactions.append(resp(self.CacheRespType, 'fl', opaque, 0, 0, 0))
    self.opaque += 1

  def get_transactions(self):
    return self.transactions
