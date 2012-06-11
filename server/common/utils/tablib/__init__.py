""" Tablib. """
import os, sys
pwd = os.path.dirname(os.path.abspath(__file__))
dotdot = os.path.join(pwd, '..')

if not pwd in sys.path:
    sys.path.append(pwd)
    
if not dotdot in sys.path:
    sys.path.append(dotdot)

from core import *
