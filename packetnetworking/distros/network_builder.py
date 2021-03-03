from ..utils import Tasks


class NetworkBuilder(Tasks):
    def __init__(self, metadata):
        self.metadata = metadata
        self.network = self.metadata.network
        self.tasks = {}
        self.dhcp = any((iface.get("dhcp") for iface in self.network.interfaces))

    def build(self):
        if self.dhcp:
            self.tasks["etc/resolv.conf"] = None

    @property
    def ipv4pub(self):
        return self.network.addresses.management.public.ipv4

    @property
    def ipv6pub(self):
        return self.network.addresses.management.public.ipv6

    @property
    def ipv4priv(self):
        return self.network.addresses.management.private.ipv4
