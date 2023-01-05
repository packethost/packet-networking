#!/usr/bin/env python3

import os
from setuptools import setup, find_packages

package_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "packetnetworking"
)


def find_templates():
    files = []
    for (path, directories, filenames) in os.walk(package_dir):
        if "templates" not in path.split(os.path.sep):
            continue
        for file in filenames:
            if not file.endswith(".j2"):
                continue
            files.append(os.path.relpath(os.path.join(path, file), package_dir))
    return files


test_reqs = ["pytest", "pytest-cov", "mock", "faker", "netaddr", "tox"]

setup(
    name="packet-networking",
    version="1.0",
    description="Tool used to setup the network files for an operating system.",
    author="Manny Mendez, Mike Mason",
    author_email="manny@packet.com, mason@packet.com",
    url="https://github.com/packethost/packet-networking/",
    packages=find_packages(),
    install_requires=[
        "click >=6.0,<7.0",
        "jinja2 >=3.1.2,<4",
        "requests >=2.21.0,<2.23",
    ],
    package_data={"packetnetworking": find_templates()},
    extras_require={"test": test_reqs},
    tests_require=test_reqs,
    entry_points="""
        [console_scripts]
        packet-networking=packetnetworking.cli:cli
    """,
)
