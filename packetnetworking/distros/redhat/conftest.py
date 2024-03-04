import pytest
from ...builder import Builder
from ... import utils
from .builder import RedhatBuilder
from .bonded import RedhatBondedNetwork
from .individual import RedhatIndividualNetwork

versions = {
    "centos": ["7"],
    "redhatenterpriseserver": ["7", "8", "9"],
}
versions = [[distro, version] for distro in versions for version in versions[distro]]


@pytest.fixture
def redhatbuilder(mockit, fake, metadata, patch_dict):
    gen_metadata = metadata

    def _builder(metadata=None, public=True):
        resolvers = ("1.2.3.4", "2.3.4.5")
        meta_interfaces = [
            {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
        ]
        phys_interfaces = [
            {"name": "enp0", "mac": "00:0c:29:51:53:a1"},
            {"name": "enp1", "mac": "00:0c:29:51:53:a2"},
        ]
        _metadata = {"network": {"interfaces": meta_interfaces}}
        if metadata:
            patch_dict(_metadata, metadata)
        md = gen_metadata(_metadata, public=public)
        with mockit(utils.get_interfaces, return_value=phys_interfaces):
            builder_metadata = Builder(md).initialize()
            builder_metadata.network.resolvers = resolvers

        return RedhatBuilder(builder_metadata)

    return _builder


@pytest.fixture(params=["bonded", "mlag_ha"])
def generic_redhat_bonded_network(redhatbuilder, patch_dict, request):
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
        builder = redhatbuilder(metadata, public=public)
        builder.build()
        builder.builders = [
            builder
            for builder in builder.builders
            if isinstance(builder, RedhatBondedNetwork)
        ]
        return builder

    return _builder


@pytest.fixture
def generic_redhat_individual_network(redhatbuilder, patch_dict):
    def _builder(distro, version, public=True, metadata=None):
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
        builder = redhatbuilder(metadata, public=public)
        builder.build()
        builder.builders = [
            builder
            for builder in builder.builders
            if isinstance(builder, RedhatIndividualNetwork)
        ]
        return builder

    return _builder
