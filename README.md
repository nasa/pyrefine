# Description

A python module for driving the CAD-to-Solution workflow based on [refine](https://github.com/nasa/refine) with [Engineering Sketch Pad](https://acdl.mit.edu/ESP/).

# Set up
## In place usage of pyrefine using pip
From this root directory do `pip install -e .` to do a "developer install". This allows you to edit pyrefine without
having to reinstall to get new changes.

## In place usage of pyrefine
Add this pyrefine root directory to your PYTHONPATH environment variable.
To use the monitoring GUIs, add the ./pyrefine/monitoring directory to your PATH environment variable.

## Installation with setup.py

setup.py in the root directory is a setuptools script for installing pyrefine.
It is run with `python setup.py install`.
Typical command line arguments to this script are `--user` to install in ~/.local or `--prefix={path/to/install}`.

# Documentation
The pyrefine documentation is generated from the source code with Sphinx.
If you do not already have sphinx installed, you can use `pip` or `conda` to install it.
Once you have installed or added pyrefine to your PYTHONPATH, the documentation is built by running `make html` in the docs directory.
The generated documentation will be in `docs/build/html`.


# Quick Start

After installation,

```
cd examples/onera_m6/geometry
./om6ste.sh
cd ../steady_sa
```

On K, run:
```
python adapt.py
```

On pfe, set your group name in `adapt_nas.py` then run the script:
```
python adapt_nas.py
```
In both cases the scripts are run from the login nodes and will launch pbs jobs for refine, fun3d, etc.


# License Notices and Disclaimers

Notices: Copyright 2022 United States Government as represented by the
Administrator of the National Aeronautics and Space Administration. No copyright
is claimed in the United States under Title 17, U.S. Code. All Other Rights
Reserved.

Disclaimers No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY
WARRANTY OF ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT
NOT LIMITED TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO
SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE, OR FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT
SOFTWARE WILL BE ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED,
WILL CONFORM TO THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER,
CONSTITUTE AN ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY
RESULTS, RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER
APPLICATIONS RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT
AGENCY DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE,
IF PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."

Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST THE
UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY
PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN ANY
LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH USE,
INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM, RECIPIENT'S USE
OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD HARMLESS THE UNITED
STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY PRIOR
RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR ANY SUCH
MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS AGREEMENT.
