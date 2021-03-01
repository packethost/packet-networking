from ..utils import Tasks


class NetworkBuilder(Tasks):
    def __init__(self, metadata):
        self.metadata = metadata
        self.network = self.metadata.network
        self.tasks = {}

    def build(self):
        pass

    @property
    def ipv4pub(self):
        return self.network.addresses.management.public.ipv4

    @property
    def ipv6pub(self):
        return self.network.addresses.management.public.ipv6

    @property
    def ipv4priv(self):
        return self.network.addresses.management.private.ipv4
