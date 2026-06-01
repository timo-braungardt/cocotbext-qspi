try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        __version__ = get_distribution("cocotbext-qspi").version
    except DistributionNotFound:
        __version__ = "0.0.0"
else:
    try:
        __version__ = version("cocotbext-qspi")
    except PackageNotFoundError:
        __version__ = "0.0.0"
