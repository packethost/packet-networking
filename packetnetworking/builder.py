from .metadata import Metadata
from . import utils
from .distros import get_distro_builder
from .hooks import trigger_hook
import logging
import requests

log = logging.getLogger()


class Builder(object):
    def __init__(self, metadata=None):
        self.metadata = None
        self.initialized = False

        self.network = NetworkData()

        if metadata:
            self.set_metadata(metadata)

    # Any attribute not found will attempt to pull it from metadata
    def __getattr__(self, attr):
        return getattr(self.metadata, attr)

    def load_metadata(self, url, **request_args):
        response = requests.get(url, **request_args)
        response.raise_for_status()
        self.set_metadata(response.json())
        return self

    def set_metadata(self, metadata):
        self.metadata = Metadata(metadata)
        self.metadata.operating_system = self.metadata.get(
            "operating_system", {"distro": None, "version": None}
        )
        return self.metadata

    def get_builder(self, distro):
        builder = get_distro_builder(distro)
        if not builder:
            raise LookupError("No builders found for distro '{}'".format(distro))
        return builder

    def trigger(self, hook, *args, **kwargs):
        return trigger_hook(hook, self, *args, **kwargs)

    def initialize(self):
        self.initialized = False
        if self.metadata is None:
            raise Exception("Metadata must be loaded before calling initialize")
        self.network.load(self.metadata.network)
        self.initialized = True
        self.trigger("initialized")
        return self

    def run(self, rootfs_path):
        if not self.initialized:
            raise Exception("Builder must be initialized before calling run")

        os = self.metadata.operating_system
        DistroBuilder = self.get_builder(os.distro)
        builder = DistroBuilder(self)
        builder.build()
        builder.run(rootfs_path)
        return builder


class NetworkData(object):
    def __init__(self, default_resolvers=None):
        self.nw_metadata = None
        self.bonding = None
        self.interfaces = None
        self.bonds = None
        self.addresses = None
        self.resolvers = default_resolvers

    def load(self, nw_metadata):
        self.nw_metadata = nw_metadata
        self.build_bonding()
        self.build_interfaces()
        self.build_bonds()
        self.build_addresses()
        self.build_resolvers()

    def build_bonding(self):
        self.bonding = self.nw_metadata.bonding

    def build_interfaces(self):
        self.interfaces = utils.WhereList()
        physical_ifaces = utils.get_interfaces()
        matched_ifaces = utils.get_matched_interfaces(
            self.nw_metadata.interfaces, physical_ifaces
        )
        if not matched_ifaces:
            log.debug("Physical Interfaces: {}".format(physical_ifaces))
            log.debug("Metadata Interfaces: {}".format(self.nw_metadata.interfaces))
            raise LookupError("No interfaces matched ones provided from metadata")
        self.interfaces = utils.RecursiveAttributes(matched_ifaces)

    def build_bonds(self):
        self.bonds = utils.RecursiveDictAttributes({})
        for iface in self.nw_metadata.interfaces:
            if "bond" in iface and iface.bond:
                if iface.bond not in self.bonds:
                    self.bonds[iface.bond] = [iface]
                else:
                    self.bonds[iface.bond].append(iface)

    def build_addresses(self):
        self.addresses = utils.IPAddressList(self.nw_metadata.addresses)

    def build_resolvers(self):
        self.resolvers = utils.resolvers(self.resolvers)
