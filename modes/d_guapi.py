#!/bin/python

# GU/API
#  Graphical User / Application Protocol Interface

#> Imports
from basemod import Mod
import argparse, webview              # typehints
from packaging.version import Version # compare mod versions
#</Imports

#> Hooks, etc.
def hook_factory(basehook: type):
    class Hook(basehook):
        def pre_window_created(self):
            return {
                'title': 'vintagestory-modmgr GUI',
                'confirm_close': True,
            }
    return Hook
#</Hooks, etc

#> GU/API Header >/
class GUAPI:
    __slots__ = ()
    mod = Mod
    class version:
        __slots__ = ()
        @staticmethod
        def compare(a: Mod, b: Mod):
            if (a.version < b.version): return -1
            elif (a.version > b.version): return 1
            else: return 0
        
