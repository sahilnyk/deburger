"""deburger - catch expensive code before it ships"""

from importlib.metadata import PackageNotFoundError, version

try:
	__version__ = version("deburger")
except PackageNotFoundError:
	__version__ = "0.0.0"

__author__ = "Sahil Nayak"
__email__ = "sahilnayak2056@gmail.com"

__all__ = ["__version__", "__author__", "__email__"]
