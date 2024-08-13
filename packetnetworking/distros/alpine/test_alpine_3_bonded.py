from textwrap import dedent
from ... import utils
import pytest


@pytest.fixture
def alpine_3_bonded_network(generic_alpine_bonded_network):
    def _builder(**kwargs):
        return generic_alpine_bonded_network("alpine", "3", **kwargs)

    return _builder


def test_alpine_3_public_bonded_task_etc_network_interfaces(alpine_3_bonded_network):
    """Validates /etc/network/interfaces for a public bond"""

    builder = alpine_3_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet manual

        auto eth1
        iface eth1 inet manual
            pre-up sleep 4

        auto bond0
        iface bond0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            hwaddress 00:0c:29:51:53:a1
            dns-nameservers {dns1} {dns2}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves eth0 eth1

        iface bond0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto bond0:0
        iface bond0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 10.0.0.0/8 gw {ipv4priv.gateway}
            post-down route del -net 10.0.0.0/8 gw {ipv4priv.gateway}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_private_bonded_task_etc_network_interfaces(alpine_3_bonded_network):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = alpine_3_bonded_network(public=False)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet manual

        auto eth1
        iface eth1 inet manual
            pre-up sleep 4

        auto bond0
        iface bond0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            hwaddress 00:0c:29:51:53:a1
            dns-nameservers {dns1} {dns2}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves eth0 eth1
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_public_bonded_task_etc_network_interfaces_with_custom_private_ip_space(
    alpine_3_bonded_network,
):
    """Validates /etc/network/interfaces for a public bond"""
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = alpine_3_bonded_network(public=True, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet manual

        auto eth1
        iface eth1 inet manual
            pre-up sleep 4

        auto bond0
        iface bond0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            hwaddress 00:0c:29:51:53:a1
            dns-nameservers {dns1} {dns2}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves eth0 eth1

        iface bond0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto bond0:0
        iface bond0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 172.16.0.0/12 gw {ipv4priv.gateway}
            post-down route del -net 172.16.0.0/12 gw {ipv4priv.gateway}
            post-up route add -net 192.168.5.0/24 gw {ipv4priv.gateway}
            post-down route del -net 192.168.5.0/24 gw {ipv4priv.gateway}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_private_bonded_task_etc_network_interfaces_with_custom_private_ip_space(
    alpine_3_bonded_network,
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = alpine_3_bonded_network(public=False, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet manual

        auto eth1
        iface eth1 inet manual
            pre-up sleep 4

        auto bond0
        iface bond0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            hwaddress 00:0c:29:51:53:a1
            dns-nameservers {dns1} {dns2}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves eth0 eth1
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_public_bonded_task_etc_network_interfaces_with_two_bonds(
    alpine_3_bonded_network,
):
    """
    When there are two bonds in metadata, we should see two bonds in the
    /etc/network/interfaces file.
    """
    new_meta_interfaces = [
        {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
        {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
        {"name": "eth2", "mac": "00:0c:29:51:53:a4", "bond": "bond1"},
        {"name": "eth3", "mac": "00:0c:29:51:53:a3", "bond": "bond1"},
    ]
    bond1 = {"network": {"interfaces": new_meta_interfaces}}
    builder = alpine_3_bonded_network(public=True, metadata=bond1)
    tasks = builder.render()

    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet manual

        auto eth1
        iface eth1 inet manual
            pre-up sleep 4

        auto eth2
        iface eth2 inet manual
            pre-up sleep 4

        auto eth3
        iface eth3 inet manual
            pre-up sleep 4

        auto bond0
        iface bond0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            hwaddress 00:0c:29:51:53:a1
            dns-nameservers {dns1} {dns2}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves eth0 eth1

        iface bond0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto bond0:0
        iface bond0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 10.0.0.0/8 gw {ipv4priv.gateway}
            post-down route del -net 10.0.0.0/8 gw {ipv4priv.gateway}

        auto bond1
        iface bond1 inet manual
            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves eth2 eth3
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_task_etc_modules(alpine_3_bonded_network):
    """Validates /etc/modules for a public bond"""
    builder = alpine_3_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        bonding
    """
    )
    assert tasks["etc/modules"]["file_mode"] == "a"
    assert tasks["etc/modules"]["content"] == result


def test_alpine_3_etc_resolvers_configured(alpine_3_bonded_network, fake):
    """
    Validates /etc/resolv.conf is configured correctly
    """
    builder = alpine_3_bonded_network()
    resolver1 = fake.ipv4()
    resolver2 = fake.ipv4()
    builder.network.resolvers = (resolver1, resolver2)
    tasks = builder.render()
    result = dedent(
        """\
        nameserver {resolver1}
        nameserver {resolver2}
    """
    ).format(resolver1=resolver1, resolver2=resolver2)
    assert tasks["etc/resolv.conf"] == result


def test_alpine_3_etc_hostname_configured(alpine_3_bonded_network):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = alpine_3_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        {hostname}
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hostname"] == result


def test_alpine_3_etc_hosts_configured(alpine_3_bonded_network):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = alpine_3_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        127.0.0.1	localhost	{hostname}

        # The following lines are desirable for IPv6 capable hosts
        ::1	localhost ip6-localhost ip6-loopback
        ff02::1	ip6-allnodes
        ff02::2	ip6-allrouters
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hosts"] == result


def test_alpine_3_persistent_interface_names(alpine_3_bonded_network):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/mdev.conf and /etc/mactab are generated.
    """
    builder = alpine_3_bonded_network()
    tasks = builder.render()

    mdevconf_result = dedent(
        """\
        {header}

        -SUBSYSTEM=net;DEVPATH=.*/net/.*;.*     root:root 600 @/sbin/nameif -s
    """
    ).format(header=utils.generated_header())

    mactab_result = dedent(
        """\
        {header}

        {iface0.meta_name} {iface0.mac}
        {iface1.meta_name} {iface1.mac}
        eth2 {phys_iface0.mac}
        eth3 {phys_iface1.mac}
    """
    ).format(
        header=utils.generated_header(),
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        phys_iface0=builder.network.physical_interfaces[0],
        phys_iface1=builder.network.physical_interfaces[1],
    )

    assert tasks["etc/mdev.conf"]["content"] == mdevconf_result
    assert tasks["etc/mactab"] == mactab_result
