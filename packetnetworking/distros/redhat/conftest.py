import pytest
from ...builder import Builder, OSInfo
from ... import utils
from .builder import RedhatBuilder
from .bonded import RedhatBondedNetwork


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


@pytest.fixture
def redhat_bonded_network(redhatbuilder):
    def _builder(public=True):
        os = {"slug": "centos_7", "distro": "centos", "version": "7"}
        builder = redhatbuilder({"operating_system": os}, public=public)
        osinfo = OSInfo(os["distro"], os["version"])
        builder.build(osinfo)
        for builder in builder.builders:
            if isinstance(builder, RedhatBondedNetwork):
                return builder

    return _builder
