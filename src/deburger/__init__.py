"""deburger - catch expensive code before it ships"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("deburger")
except PackageNotFoundError:
    from deburger._version import __version__

__author__ = "Sahil Nayak"
__email__ = "sahilnayak2056@gmail.com"

__all__ = ["__version__", "__author__", "__email__"]
