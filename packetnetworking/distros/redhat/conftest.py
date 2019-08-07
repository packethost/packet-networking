import pytest
import mock
from ...builder import Builder
from ... import utils
from .builder import RedhatBuilder


@pytest.fixture
def redhatbuilder(mockit, faker, metadata):
    eth0_mac = faker.mac_address()
    eth1_mac = faker.mac_address()
    meta_interfaces = [
        {'name': 'eth0', 'mac': eth0_mac, 'bond': 'bond0'},
        {'name': 'eth1', 'mac': eth1_mac, 'bond': 'bond0'},
    ]
    phys_interfaces = [
        {'name': 'enp0', 'mac': eth0_mac},
        {'name': 'enp1', 'mac': eth1_mac},
    ]
    md = metadata({'network': {'interfaces': meta_interfaces}})
    with mockit(utils.get_interfaces, return_value=phys_interfaces):
        builder_metadata = Builder(md).initialize()
    return RedhatBuilder(builder_metadata)