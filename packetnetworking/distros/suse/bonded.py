from .. import NetworkBuilder


# pylama:ignore=E501
class SuseBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "bonded":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}

        self.tasks[
            "etc/modprobe.d/bonding.conf"
        ] = """\
            alias bond0 bonding
            options bond0 mode={{ net.bonding.mode }} miimon=100 downdelay=200 updelay=200 xmit_hash_policy=layer3+4 lacp_rate=1
        """

        self.tasks[
            "etc/sysconfig/network/ifcfg-bond0"
        ] = """\
            STARTMODE='onboot'
            BOOTPROTO='static'
            IPADDR='{{ ip4pub.address }}/{{ ip4pub.cidr }}'
            BONDING_MASTER='yes'
            BONDING_SLAVE_0='{{ interfaces[0].name }}'
            BONDING_SLAVE_1='{{ interfaces[1].name }}'
            BONDING_MODULE_OPTS='mode={{ net.bonding.mode }} miimon=100'
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
            {% for subnets in private_subnets %}
            {{ subnets }}  {{ ip4priv.gateway }}
            {% endfor %}
        """

        ifcfg = """\
            STARTMODE='hotplug'
            BOOTPROTO='none'
        """
        for i in range(len(self.network.interfaces)):
            name = self.network.interfaces[i]["name"]
            cfg = ifcfg.format(iface=name, i=i)
            self.tasks["etc/sysconfig/network/ifcfg-" + name] = cfg

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
