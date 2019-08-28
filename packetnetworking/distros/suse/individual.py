from .. import NetworkBuilder


# pylama:ignore=E501
class SuseIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "individual":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}

        iface0 = self.network.interfaces[0]

        self.tasks[
            "etc/sysconfig/network/ifcfg-" + iface0.name
        ] = """\
            STARTMODE='onboot'
            BOOTPROTO='static'
            IPADDR='{{ ip4pub.address }}/{{ ip4pub.cidr }}'
            IPADDR1='{{ ip4priv.address }}'
            NETMASK1='{{ ip4priv.netmask }}'
            GATEWAY1='{{ ip4priv.gateway }}'
            LABEL1='0'
            IPADDR2='{{ ip6pub.address }}/{{ ip6pub.cidr }}'
            GATEWAY2='{{ ip6pub.gateway }}'
            LABEL2='1'
        """

        self.tasks[
            "etc/sysconfig/network/routes"
        ] = """\
            default     {{ ip4pub.gateway }}
            10.0.0.0/8  {{ ip4priv.gateway }}
        """

        ifcfg = """\
            STARTMODE='hotplug'
            BOOTPROTO='none'
        """
        for i, iface in enumerate(self.network.interfaces):
            if iface == iface0:
                # skip interface since it is already configured above
                continue
            cfg = ifcfg.format(iface=iface.name, i=i)
            self.tasks["etc/sysconfig/network/ifcfg-" + iface.name] = cfg

        self.tasks[
            "etc/resolv.conf"
        ] = """\
            {% for server in resolvers %}
            nameserver {{ server }}
            {% endfor %}
        """

        self.tasks[
            "etc/hostname"
        ] = """\
            {{ hostname }}
        """

        self.tasks[
            "etc/hosts"
        ] = """\
            127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
            ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
        """
        return self.tasks
