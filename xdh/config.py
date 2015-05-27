"""
Base module for making config objects
"""

import sys

from xdh import _config

config = _config.MainConfig()
config.__doc__ = __doc__
sys.modules[__name__] = config