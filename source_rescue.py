# License: GPL2 or later see COPYING
# Written by Masatake YAMATO
# Copyright (C) 2010, 2012 Masatake YAMATO <yamato@redhat.com>

# python library imports

# our imports
from mockbuild.trace_decorator import decorate, traceLog, getLog

import mockbuild.util
import sys
import glob
import shutil
import os

requires_api_version = "1.0"

# plugin entry point
decorate(traceLog())
def init(root, opts):
    SourceRescue(root, opts)

class SourceSOS (Exception):
    """Trigger to jump finally block"""
    pass

class SourceRescue(object):
    """Rescuing rpmbuild -bp result"""
    decorate(traceLog())
    def __init__(self, root, opts):
        self.result = -2
        self.root = root
        self.opts = opts
        self.shelterdir = opts.get("shelterdir", False) or (root.resultdir + "/" + "srpmix")
        self.dont_make_patch_backup = opts.get("dont_make_patch_backup", True)
        self.salt = '.' + 'df6056a7-d1fc-4cc3-b831-6aac00e7f73a'
        if not self.shelterdir:
            raise RuntimeError, "Neither \"shelterdir\" config parameter nor \"resultdir\" config parameter given"
        if os.path.exists(self.shelterdir):
            raise RuntimeError, "%s already exists"%self.shelterdir

        root.addHook("prebuild",  self.prebuild)
        root.addHook("postbuild", self.postbuild)

    decorate(traceLog())
    def prebuild(self):
        root = self.root

        specs = glob.glob(root.makeChrootPath(root.builddir, "SPECS", "*.spec"))
        spec = specs[0]
        self.wash_spec(spec)
            
        getLog().info("Synthesizing source code")
        chrootspec = spec.replace(root.makeChrootPath(), '') # get rid of rootdir prefix
        try:
            root.doChroot(
                ["bash", "--login", "-c", 'rpmbuild -bp --target %s --nodeps %s' % (root.rpmbuild_arch, 
                                                                                    chrootspec)],
                shell=False,
                logger=root.build_log, 
                timeout=0,
                uid=root.chrootuid,
                gid=root.chrootgid,
                raiseExc=True
                )
        except:
            getLog().info("Failed in synthesizing")
            self.result = -1
            raise SourceSOS

        getLog().info("Rescuing source code to %s" % self.shelterdir)
        bd_out = root.makeChrootPath(root.builddir)
        os.system("chmod -R a+r %s"%bd_out)
        os.system("find %s -type d -print0 | xargs -0 chmod a+x"%bd_out)
        shutil.copytree(bd_out, self.shelterdir, symlinks=True)
        os.system("find %s -name '*%s' -print0 | xargs -0 rm -f"%(self.shelterdir, self.salt))
        os.system ("mv %sb %s" % (spec, spec))
        self.result = 0
        raise SourceSOS
    
    decorate(traceLog())
    def wash_spec(self, spec):
        if self.dont_make_patch_backup:
            self.wash__dont_make_patch_backup(spec)

    decorate(traceLog())        
    def wash__dont_make_patch_backup(self, spec):
        os.system ("cp %s %sb"  % (spec, spec))
        sed = "sed -i -e 's/\\(^%%patch[0-9]\\+.*\\)[ \\t]-b[ \\t]\+[^ \\t]\+\\(.*\\)/\\1 -b %s \\2/' %s"
        os.system(sed % (self.salt, spec))

    decorate(traceLog())
    def postbuild(self):
        self.root.clean()
        sys.exit(self.result)

# mock --resultdir=/tmp/tomcat6 --enable-plugin=source_rescue -r epel-4-x86_64 --rebuild /srv/sources/attic/cradles/ftp.redhat.com/mirror/linux/enterprise/4/en/os/x86_64/SRPMS/unixODBC-2.2.9-1.src.rpm
