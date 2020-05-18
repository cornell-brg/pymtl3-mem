import os
import sys
import pytest
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) )

def pytest_addoption(parser):
  parser.addoption( "--line-trace", action="store", default=1, choices=[0,1,2], type=int,
                    help="verbosity of line trace" )

@pytest.fixture
def line_trace(request):
  return request.config.option.line_trace


def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

#-------------------------------------------------------------------------
# Handle other command line options
#-------------------------------------------------------------------------

def pytest_configure(config):
  random.seed(0xdeadbeef)

def pytest_unconfigure(config):
  pass
