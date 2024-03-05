import textwrap

import pytest

from ...builder import Builder
from ... import utils
from .builder import DebianBuilder
from .bonded import DebianBondedNetwork
from .individual import DebianIndividualNetwork


versions = {
    "debian": ["10", "11", "12"],
    "ubuntu": ["18.04", "20.04", "22.04"],
}
versions = [[distro, version] for distro in versions for version in versions[distro]]


@pytest.fixture
def expected_file_etc_network_interfaces_dhcp_2():
    expected_file_etc_network_interfaces_dhcp_2 = textwrap.dedent(
        """\
        auto lo
        iface lo inet loopback

        auto enp0
        iface enp0 inet dhcp

        auto enp1
        iface enp1 inet dhcp

    """
    )
    yield expected_file_etc_network_interfaces_dhcp_2


@pytest.fixture(
    ids=[
        "1bond2nics",
        "1bond4nics",
        "2bonds2nics",
    ],
    params=[
        [
            {"name": "eth0", "mac": "00:0c:29:51:53:a0", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
        ],
        [
            {"name": "eth0", "mac": "00:0c:29:51:53:a0", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth2", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
            {"name": "eth3", "mac": "00:0c:29:51:53:a3", "bond": "bond0"},
        ],
        [
            {"name": "eth0", "mac": "00:0c:29:51:53:a0", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth2", "mac": "00:0c:29:51:53:a2", "bond": "bond1"},
            {"name": "eth3", "mac": "00:0c:29:51:53:a3", "bond": "bond1"},
        ],
    ],
)
def debianbuilder(mockit, fake, metadata, patch_dict, request):
    gen_metadata = metadata

    def _builder(metadata=None, public=True, post_gen_metadata=None):
        resolvers = ("1.2.3.4", "2.3.4.5")
        meta_interfaces = request.param
        phys_interfaces = [
            {"name": iface["name"].replace("eth", "enp"), "mac": iface["mac"]}
            for iface in meta_interfaces
        ]
        _metadata = {"network": {"interfaces": meta_interfaces}}
        if metadata:
            patch_dict(_metadata, metadata)
        md = gen_metadata(_metadata, public=public)
        if post_gen_metadata:
            md = post_gen_metadata(md)
        with mockit(utils.get_interfaces, return_value=phys_interfaces):
            builder_metadata = Builder(md).initialize()
            builder_metadata.network.resolvers = resolvers

        return DebianBuilder(builder_metadata)

    return _builder


@pytest.fixture(params=["bonded", "mlag_ha"])
def generic_debian_bonded_network(debianbuilder, patch_dict, request):
    def _builder(distro, version, public=True, metadata=None):
        version = str(version)
        slug = "{distro}_{version}".format(distro=distro, version=version)
        metadata = patch_dict(
            {
                "network": {"bonding": {"link_aggregation": request.param}},
                "operating_system": {
                    "slug": slug,
                    "distro": distro,
                    "version": version,
                },
            },
            metadata or {},
        )
        builder = debianbuilder(metadata, public=public)
        builder.build()
        builder.builders = [
            builder
            for builder in builder.builders
            if isinstance(builder, DebianBondedNetwork)
        ]
        return builder

    return _builder


@pytest.fixture
def generic_debian_individual_network(debianbuilder, patch_dict):
    def _builder(distro, version, public=True, metadata=None, **kwargs):
        version = str(version)
        slug = "{distro}_{version}".format(distro=distro, version=version)
        metadata = patch_dict(
            {
                "network": {"bonding": {"link_aggregation": "individual"}},
                "operating_system": {
                    "slug": slug,
                    "distro": distro,
                    "version": version,
                },
            },
            metadata or {},
        )
        builder = debianbuilder(metadata, public=public, **kwargs)
        builder.build()
        builder.builders = [
            builder
            for builder in builder.builders
            if isinstance(builder, DebianIndividualNetwork)
        ]
        return builder

    return _builder
