# PyMTL3 Memory
Project repo for cache/memory related components implemented in pymtl3


## PyMTL3 Installation
On a Python3 virtual environment:
```
% git clone git@github.com:cornell-brg/pymtl3.git
% pip install --editable ./pymtl3
% pip install --upgrade pytest
```

## Running Tests
```
% git clone git@github.com:cornell-brg/pymtl3-mem.git
% cd pymtl3-mem
% mkdir build && cd build
% pytest --disable-pytest-warnings ../BlockingCache/test/BlockingCacheRTL_test.py -v
```
pytest warnings occur as a result of classes with "test" in its name
