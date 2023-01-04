from textwrap import dedent
from ... import utils
import pytest


@pytest.fixture
def alpine_3_individual_network(generic_alpine_individual_network):
    def _builder(**kwargs):
        return generic_alpine_individual_network("alpine", "3", **kwargs)

    return _builder


def test_alpine_3_public_individual_task_etc_network_interfaces(
    alpine_3_individual_network,
):
    """Validates /etc/network/interfaces for a public bond"""

    builder = alpine_3_individual_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            dns-nameservers {dns1} {dns2}

        iface eth0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto eth0:0
        iface eth0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 10.0.0.0/8 gw {ipv4priv.gateway}
            post-down route del -net 10.0.0.0/8 gw {ipv4priv.gateway}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_private_individual_task_etc_network_interfaces(
    alpine_3_individual_network,
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = alpine_3_individual_network(public=False)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            dns-nameservers {dns1} {dns2}
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_public_individual_task_etc_network_interfaces_with_custom_private_ip_space(
    alpine_3_individual_network,
):
    """Validates /etc/network/interfaces for a public bond"""
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = alpine_3_individual_network(public=True, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            dns-nameservers {dns1} {dns2}

        iface eth0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto eth0:0
        iface eth0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 192.168.5.0/24 gw {ipv4priv.gateway}
            post-down route del -net 192.168.5.0/24 gw {ipv4priv.gateway}
            post-up route add -net 172.16.0.0/12 gw {ipv4priv.gateway}
            post-down route del -net 172.16.0.0/12 gw {ipv4priv.gateway}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_private_individual_task_etc_network_interfaces_with_custom_private_ip_space(
    alpine_3_individual_network,
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = alpine_3_individual_network(public=False, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            dns-nameservers {dns1} {dns2}
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_etc_resolvers_configured(alpine_3_individual_network, fake):
    """
    Validates /etc/resolv.conf is configured correctly
    """
    builder = alpine_3_individual_network()
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


def test_alpine_3_etc_hostname_configured(alpine_3_individual_network):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = alpine_3_individual_network()
    tasks = builder.render()
    result = dedent(
        """\
        {hostname}
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hostname"] == result


def test_alpine_3_etc_hosts_configured(alpine_3_individual_network):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = alpine_3_individual_network()
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


def test_alpine_3_persistent_interface_names(alpine_3_individual_network):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/mdev.conf and /etc/mactab are generated.
    """
    builder = alpine_3_individual_network()
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


def test_alpine_3_public_individual_dhcp_task_etc_network_interfaces(
    alpine_3_individual_network,
    make_interfaces_dhcp_metadata,
    expected_file_etc_network_interfaces_dhcp_2,
):
    """Validates /etc/network/interfaces for a public dhcp interfaces"""

    builder = alpine_3_individual_network(
        public=True, post_gen_metadata=make_interfaces_dhcp_metadata
    )
    tasks = builder.render()

    result = expected_file_etc_network_interfaces_dhcp_2

    assert tasks["etc/network/interfaces"] == result


def test_alpine_3_etc_resolvers_dhcp(
    alpine_3_individual_network, make_interfaces_dhcp_metadata
):
    """
    Validates /etc/resolv.conf is skipped
    """
    builder = alpine_3_individual_network(
        post_gen_metadata=make_interfaces_dhcp_metadata
    )
    tasks = builder.render()
    assert tasks["etc/resolv.conf"] is None
