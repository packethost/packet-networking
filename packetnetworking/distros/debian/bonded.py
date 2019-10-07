from .. import NetworkBuilder
from ...utils import generate_persistent_names


# pylama:ignore=E501
class DebianBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "bonded":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}
        self.tasks[
            "etc/network/interfaces"
        ] = """\
            auto lo
            iface lo inet loopback

            auto bond0
            iface bond0 inet static
                {% if ip4pub %}
                address {{ ip4pub.address }}
                netmask {{ ip4pub.netmask }}
                gateway {{ ip4pub.gateway }}
                {% else %}
                address {{ ip4priv.address }}
                netmask {{ ip4priv.netmask }}
                gateway {{ ip4priv.gateway }}
                {% endif %}
                bond-downdelay 200
                bond-miimon 100
                bond-mode {{ net.bonding.mode }}
                bond-updelay 200
                bond-xmit_hash_policy layer3+4
                {% if osinfo.distro == 'ubuntu' and net.bonding.mode == 4 %}
                bond-lacp-rate 1
                {% endif %}
                bond-slaves{% for iface in interfaces %} {{ iface.name }}{% endfor %}

                dns-nameservers{% for dns in resolvers %} {{ dns }}{% endfor %}

            {% if ip6pub %}
            iface bond0 inet6 static
                address {{ ip6pub.address }}
                netmask {{ ip6pub.cidr }}
                gateway {{ ip6pub.gateway }}
            {% endif %}

            {% if ip4pub %}
            auto bond0:0
            iface bond0:0 inet static
                address {{ ip4priv.address }}
                netmask {{ ip4priv.netmask }}
                {% for subnet in private_subnets %}
                post-up route add -net {{ subnet }} gw {{ ip4priv.gateway }}
                post-down route del -net {{ subnet }} gw {{ ip4priv.gateway }}
                {% endfor %}
            {% endif %}
            {% if osinfo.distro == 'ubuntu' %}
            {% for iface in interfaces %}

            auto {{ iface.name }}
            iface {{ iface.name }} inet manual
            {% if iface.name != interfaces[0].name %}
                pre-up sleep 4
            {% endif %}
                bond-master bond0
            {% endfor %}
            {% endif %}
        """

        self.tasks["etc/modules"] = {
            "file_mode": "a",
            "template": """\
            bonding
        """,
        }

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
