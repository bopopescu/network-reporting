""" Tablib. """
import os, sys
pwd = os.path.dirname(os.path.abspath(__file__))
dotdot = os.path.join(pwd, '..')
sys.path.append(pwd)
sys.path.append(dotdot)

from core import *
