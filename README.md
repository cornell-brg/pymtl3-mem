# PyMTL3 Memory
Project repo for cache/memory related components implemented in pymtl3


## PyMTL3 
### Create virtual environment

While not strictly necessary, we strongly recommend using [virtualenv][5]
to install PyMTL3 and the Python packages that PyMTL3 depends on.
virtualenv enables creating isolated Python environments. The following
commands will create and activate the virtual environment:

```
 % python3 -m venv ${HOME}/venv
 % source ${HOME}/venv/bin/activate
```

 [5]: https://virtualenv.pypa.io/en/latest/

### Install PyMTL3
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
% pytest ../BlockingCache/test/BlockingCacheRTL_test.py -v
```
