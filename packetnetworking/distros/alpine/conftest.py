import textwrap

import pytest

from ...builder import Builder
from ... import utils
from .builder import AlpineBuilder
from .bonded import AlpineBondedNetwork
from .individual import AlpineIndividualNetwork


@pytest.fixture
def expected_file_etc_network_interfaces_dhcp_2():
    expected_file_etc_network_interfaces_dhcp_2 = textwrap.dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet dhcp

        auto eth1
        iface eth1 inet dhcp

    """
    )
    yield expected_file_etc_network_interfaces_dhcp_2


@pytest.fixture
def alpinebuilder(mockit, fake, metadata, patch_dict):
    gen_metadata = metadata

    def _builder(metadata=None, public=True, post_gen_metadata=None):
        resolvers = ("1.2.3.4", "2.3.4.5")
        meta_interfaces = [
            {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
        ]
        phys_interfaces = [
            {"name": "enp0", "mac": "00:0c:29:51:53:a4"},
            {"name": "enp1", "mac": "00:0c:29:51:53:a3"},
            {"name": "enp2", "mac": "00:0c:29:51:53:a1"},
            {"name": "enp3", "mac": "00:0c:29:51:53:a2"},
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

        return AlpineBuilder(builder_metadata)

    return _builder


@pytest.fixture(params=["bonded", "mlag_ha"])
def generic_alpine_bonded_network(alpinebuilder, patch_dict, request):
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
        builder = alpinebuilder(metadata, public=public)
        builder.build()
        builder.builders = [
            builder
            for builder in builder.builders
            if isinstance(builder, AlpineBondedNetwork)
        ]
        return builder

    return _builder


@pytest.fixture
def generic_alpine_individual_network(alpinebuilder, patch_dict):
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
        builder = alpinebuilder(metadata, public=public, **kwargs)
        builder.build()
        builder.builders = [
            builder
            for builder in builder.builders
            if isinstance(builder, AlpineIndividualNetwork)
        ]
        return builder

    return _builder
