import os

try:
    __import__('py2exe')
except ImportError:
    import sys

    if 'py2exe' in sys.argv:
        sys.exit("You need to run `python setup.py install` prior to using py2exe.")

from glob import glob
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


MSVC90_ARCH_PREFIX = 'x86'  # TODO: Consider trying 'amd64'

data_files = [
    ("Microsoft.VC90.CRT", glob(os.environ["WinDir"] + rf'\\WinSxS\{MSVC90_ARCH_PREFIX}_microsoft.vc90.crt_*\\*.*'),),
    (".", ['vdimonitor.ini', 'logging.ini'])
]

script = os.path.join('windowsprocessmonitor', 'vdimonitor.py')

setup(
    name="A Windows process monitor",
    version="0.0.1",
    author="Arek Glinka",
    author_email="arekglinka@gmail.com",
    description="A tool monitoring if a process is running and displaying a dialog if not.",
    license="BSD",
    keywords="windows process monitor",
    url="http://github.com/arekglinka/windowsprocessmonitor",
    packages=['windowsprocessmonitor', 'tests'],
    install_requires=read('requirements.txt').splitlines(),
    extras_require={
        'dev': [
            'pytest',
            'mock',
        ]
    },
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    console=[script],
    options={
        'py2exe': {
            'bundle_files': 2,
            'compressed': True,
        }
    },
    zipfile=None,
    data_files=data_files
)
