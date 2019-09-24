from .. import NetworkBuilder
from ...utils import generate_persistent_names


# pylama:ignore=E501
class DebianIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "individual":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}
        self.tasks[
            "etc/network/interfaces"
        ] = """\
            auto lo
            iface lo inet loopback

            auto {{ iface0.name }}
            iface {{ iface0.name }} inet static
                {% if ip4pub %}
                address {{ ip4pub.address }}
                netmask {{ ip4pub.netmask }}
                gateway {{ ip4pub.gateway }}
                {% else %}
                address {{ ip4priv.address }}
                netmask {{ ip4priv.netmask }}
                gateway {{ ip4priv.gateway }}
                {% endif %}

                dns-nameservers{% for dns in resolvers %} {{ dns }}{% endfor %}

            {% if ip6pub %}
            iface {{ iface0.name }} inet6 static
                address {{ ip6pub.address }}
                netmask {{ ip6pub.cidr }}
                gateway {{ ip6pub.gateway }}
            {% endif %}

            {% if ip4pub %}
            auto {{ iface0.name }}:0
            iface {{ iface0.name }}:0 inet static
                address {{ ip4priv.address }}
                netmask {{ ip4priv.netmask }}
                {% for subnet in private_subnets %}
                post-up route add -net {{ subnet }} gw {{ ip4priv.gateway }}
                post-down route del -net {{ subnet }} gw {{ ip4priv.gateway }}
                {% endfor %}
            {% endif %}
        """

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
            127.0.0.1	localhost	{{ hostname }}

            # The following lines are desirable for IPv6 capable hosts
            ::1	localhost ip6-localhost ip6-loopback
            ff02::1	ip6-allnodes
            ff02::2	ip6-allrouters
        """

        if self.metadata.operating_system.version == "14.04":
            self.tasks.update(generate_persistent_names())
        return self.tasks
