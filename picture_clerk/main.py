#!/usr/bin/env python
from __future__ import with_statement
"""pic.py

PictureClerk - The little helper for your picture workflow.
Start script
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/08/05 $"
__copyright__ = "Copyright (c) 2008 Matthias Grueter"
__license__ = "GPL"


# TODO: use explicit relative imports
import pic


if __name__ == "__main__":
    import sys
    try:
        pic.main()
    except KeyboardInterrupt:
        # FIXME: kill threads, wait for them and then exit
        print "Exiting."
        sys.exit(None)
