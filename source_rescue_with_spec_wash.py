# License: GPL2 or later see COPYING
# Written by Masatake YAMATO
# Copyright (C) 2010, 2012 Masatake YAMATO <yamato@redhat.com>

# python library imports

# our imports
from mockbuild.trace_decorator import decorate, traceLog, getLog

import mockbuild.util
import mockbuild.plugins.source_rescue
import os

requires_api_version = "1.0"

# plugin entry point
decorate(traceLog())
def init(root, opts):
    SourceRescueWithSpecWash(root, opts)

class SourceRescueWithSpecWash(SourceRescue):
    """Do the same as SourceRescue but trying to remove patch back files"""
    decorate(traceLog())
    def __init__(self, root, opts):
        SourceRescue.__init__(self)

    decorate(traceLog())
    def wash_spec(self, spec):
        sed = "sed -i -e 's/\(^%patch[0-9]\+.*\)[ \t]-b[ \t]\+[^ \t]\+\(.*\)/\1 \2/' %s"
        os.system(sed % spec)
    

