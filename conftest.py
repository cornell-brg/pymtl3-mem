import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) )

def pytest_addoption(parser):
  parser.addoption( "--line-trace", action="store", default=1, choices=[0,1,2], type=int,
                    help="verbosity of line trace" )
  parser.addoption( "--max-cycles", action="store", type=int, default=20000,
                    help="max number of cycles to be simulated" )
  parser.addoption( "--dump-vtb", action="store_true",
                    help="dump verilog test bench for each test")

@pytest.fixture
def line_trace(request):
  return request.config.option.line_trace

@pytest.fixture
def max_cycles(request):
  """Max number of simulation cycles."""
  return request.config.option.max_cycles

@pytest.fixture
def dump_vtb(request):
  """Dump Verilog test bench for each test"""
  if request.config.option.dump_vtb:
    assert request.config.option.test_verilog, "--dump-vtb requires --test-verilog"
    test_module = request.module.__name__
    test_name   = request.node.name
    test_name   = test_name.replace("-", "_")
    test_name   = test_name.replace("[", "_")
    test_name   = test_name.replace("]", "")
    return '{}'.format( test_name )
  else:
    return None

def pytest_configure(config):
  import sys
  sys._called_from_test = True
  if config.option.dump_vcd:
    sys._pymtl_dump_vcd = True
  else:
    sys._pymtl_dump_vcd = False

def pytest_unconfigure(config):
  import sys
  del sys._called_from_test
  del sys._pymtl_dump_vcd

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

def pytest_runtest_setup(item):
  test_verilog = item.config.option.test_verilog
  if test_verilog and 'test_verilog' not in item.fixturenames:
    pytest.skip("ignoring non-Verilog tests")
