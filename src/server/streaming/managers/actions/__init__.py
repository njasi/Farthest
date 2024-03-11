"""
Organize all of the actions we can send to a Channel Manager into a small module.

TODO make telegram & flask varients
thats how I imagine it working at least
"""

from .ChannelAction import ChannelAction
from .Add import Add
from .Play import Play
from .Pause import Pause
from .Skip import Skip
