#> Imports
try: import tkinter as tk # base graphics UI
except: tk = False
import argparse           # type hinting

from basemod import Mod
#</Imports

#> Header >/
class GUI:
    @classmethod
    def command(cls, ns: argparse.Namespace):
        ...
