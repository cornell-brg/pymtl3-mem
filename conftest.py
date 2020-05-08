import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) )

def pytest_addoption(parser):
  parser.addoption( "--line-trace", action="store", default=1, choices=[0,1,2], type=int,
                    help="verbosity of line trace" )
  parser.addoption( "--max-cycles", action="store", type=int, default=20000,
                    help="max number of cycles to be simulated" )

@pytest.fixture
def line_trace(request):
  return request.config.option.line_trace

@pytest.fixture
def max_cycles(request):
  """Max number of simulation cycles."""
  return request.config.option.max_cycles

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True
