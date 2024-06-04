from textwrap import dedent
from .conftest import versions
import pytest


@pytest.fixture
def bonded_network_builder(generic_debian_bonded_network):
    def _builder(distro, version, **kwargs):
        return generic_debian_bonded_network(distro, version, **kwargs)

    return _builder


@pytest.mark.parametrize("distro,version", versions)
def test_public_bonded_task_etc_network_interfaces(
    bonded_network_builder, distro, version
):
    """Validates /etc/network/interfaces for a public bond"""

    builder = bonded_network_builder(distro, version, public=True)
    tasks = builder.render()

    bonding_mode = builder.network.bonding.mode
    ipv4priv = builder.ipv4priv.first
    ipv4pub = builder.ipv4pub.first
    ipv6pub = builder.ipv6pub.first
    partial = """\
        auto lo
        iface lo inet loopback
        """
    result = dedent(partial)
    for iface in sorted(builder.network.interfaces, key=lambda iface: iface.name):
        if iface.name != builder.network.interfaces[0].name:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    pre-up sleep 4
                    bond-master {iface.bond}
                """
        else:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    bond-master {iface.bond}
                """
        result += dedent(partial)
    partial = f"""
        auto bond0
        iface bond0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            hwaddress {builder.network.interfaces[0].mac}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
        """
    result += dedent(partial)
    result += "    bond-lacp-rate 1\n"
    result += f"""    bond-slaves {' '.join(sorted(nic.name for nic in builder.network.bonds["bond0"]))}\n"""

    partial = f"""
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
    result += dedent(partial)

    for bond, members in builder.network.bonds.items():
        if bond == "bond0":
            continue

        partial = f"""
            auto {bond}
            iface {bond} inet manual
                bond-downdelay 200
                bond-miimon 100
                bond-mode {bonding_mode}
                bond-updelay 200
                bond-xmit_hash_policy layer3+4
            """
        result += dedent(partial)
        result += "    bond-lacp-rate 1\n"
        result += f"    bond-slaves {' '.join(sorted(nic.name for nic in members))}\n"
    assert tasks["etc/network/interfaces"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_bonded_task_etc_network_interfaces(
    bonded_network_builder, distro, version
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = bonded_network_builder(distro, version, public=False)
    tasks = builder.render()

    bonding_mode = builder.network.bonding.mode
    ipv4priv = builder.ipv4priv.first
    partial = """\
        auto lo
        iface lo inet loopback
        """
    result = dedent(partial)
    for iface in sorted(builder.network.interfaces, key=lambda iface: iface.name):
        if iface.name != builder.network.interfaces[0].name:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    pre-up sleep 4
                    bond-master {iface.bond}
                """
        else:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    bond-master {iface.bond}
                """
        result += dedent(partial)
    partial = f"""
        auto bond0
        iface bond0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            hwaddress {builder.network.interfaces[0].mac}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
        """
    result += dedent(partial)
    result += "    bond-lacp-rate 1\n"
    result += f"    bond-slaves {' '.join(sorted(nic.name for nic in builder.network.bonds['bond0']))}\n"

    for bond, members in builder.network.bonds.items():
        if bond == "bond0":
            continue

        partial = f"""
            auto {bond}
            iface {bond} inet manual
                bond-downdelay 200
                bond-miimon 100
                bond-mode {bonding_mode}
                bond-updelay 200
                bond-xmit_hash_policy layer3+4
            """
        result += dedent(partial)
        result += "    bond-lacp-rate 1\n"
        result += f"    bond-slaves {' '.join(sorted(nic.name for nic in members))}\n"
    assert tasks["etc/network/interfaces"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_public_bonded_task_etc_network_interfaces_with_custom_private_ip_space(
    bonded_network_builder, distro, version
):
    """Validates /etc/network/interfaces for a public bond"""
    subnets = {"private_subnets": reversed(["192.168.5.0/24", "172.16.0.0/12"])}
    builder = bonded_network_builder(distro, version, public=True, metadata=subnets)
    tasks = builder.render()

    bonding_mode = builder.network.bonding.mode
    ipv4priv = builder.ipv4priv.first
    ipv4pub = builder.ipv4pub.first
    ipv6pub = builder.ipv6pub.first
    partial = """\
        auto lo
        iface lo inet loopback
        """
    result = dedent(partial)
    for iface in sorted(builder.network.interfaces, key=lambda iface: iface.name):
        if iface.name != builder.network.interfaces[0].name:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    pre-up sleep 4
                    bond-master {iface.bond}
                """
        else:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    bond-master {iface.bond}
                """
        result += dedent(partial)
    partial = f"""
        auto bond0
        iface bond0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            hwaddress {builder.network.interfaces[0].mac}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
        """
    result += dedent(partial)
    result += "    bond-lacp-rate 1\n"
    result += f"""    bond-slaves {' '.join(sorted(nic.name for nic in builder.network.bonds["bond0"]))}\n"""
    partial = f"""
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
    result += dedent(partial)

    for bond, members in builder.network.bonds.items():
        if bond == "bond0":
            continue

        partial = f"""
            auto {bond}
            iface {bond} inet manual
                bond-downdelay 200
                bond-miimon 100
                bond-mode {bonding_mode}
                bond-updelay 200
                bond-xmit_hash_policy layer3+4
            """
        result += dedent(partial)
        result += "    bond-lacp-rate 1\n"
        result += f"    bond-slaves {' '.join(sorted(nic.name for nic in members))}\n"
    assert tasks["etc/network/interfaces"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_bonded_task_etc_network_interfaces_with_custom_private_ip_space(
    bonded_network_builder, distro, version
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = bonded_network_builder(distro, version, public=False)
    tasks = builder.render()

    bonding_mode = builder.network.bonding.mode
    ipv4priv = builder.ipv4priv.first
    partial = """\
        auto lo
        iface lo inet loopback
        """
    result = dedent(partial)
    for iface in sorted(builder.network.interfaces, key=lambda iface: iface.name):
        if iface.name != builder.network.interfaces[0].name:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    pre-up sleep 4
                    bond-master {iface.bond}
                """
        else:
            partial = f"""
                auto {iface.name}
                iface {iface.name} inet manual
                    bond-master {iface.bond}
                """
        result += dedent(partial)
    partial = f"""
        auto bond0
        iface bond0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            hwaddress {builder.network.interfaces[0].mac}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}

            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
        """
    result += dedent(partial)
    result += "    bond-lacp-rate 1\n"
    result += f"""    bond-slaves {' '.join(sorted(nic.name for nic in builder.network.bonds["bond0"]))}\n"""

    for bond, members in builder.network.bonds.items():
        if bond == "bond0":
            continue

        partial = f"""
            auto {bond}
            iface {bond} inet manual
                bond-downdelay 200
                bond-miimon 100
                bond-mode {bonding_mode}
                bond-updelay 200
                bond-xmit_hash_policy layer3+4
            """
        result += dedent(partial)
        result += "    bond-lacp-rate 1\n"
        result += f"    bond-slaves {' '.join(sorted(nic.name for nic in members))}\n"
    assert tasks["etc/network/interfaces"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_task_etc_modules(bonded_network_builder, distro, version):
    """Validates /etc/modules for a public bond"""
    builder = bonded_network_builder(distro, version, public=True)
    tasks = builder.render()

    result = "bonding\n"
    assert tasks["etc/modules"]["file_mode"] == "a"
    assert tasks["etc/modules"]["content"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_etc_systemd_resolved_configured(bonded_network_builder, fake, distro, version):
    """
    Validates /etc/systemd/resolved.conf is configured correctly
    """
    builder = bonded_network_builder(distro, version)
    resolver1 = fake.ipv4()
    resolver2 = fake.ipv4()
    builder.network.resolvers = (resolver1, resolver2)
    tasks = builder.render()
    if distro == "ubuntu":
        result = f"""\
            [Resolve]
            DNS={resolver1} {resolver2}
        """
        assert tasks["etc/systemd/resolved.conf"] == dedent(result)
        assert "etc/resolv.conf" not in tasks
    else:
        result = f"""\
            nameserver {resolver1}
            nameserver {resolver2}
        """
        assert tasks["etc/resolv.conf"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_etc_hostname_configured(bonded_network_builder, distro, version):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = bonded_network_builder(distro, version)
    tasks = builder.render()

    hostname = builder.metadata.hostname
    result = f"{hostname}\n"
    assert tasks["etc/hostname"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_etc_hosts_configured(bonded_network_builder, distro, version):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = bonded_network_builder(distro, version)
    tasks = builder.render()

    hostname = builder.metadata.hostname
    result = f"""\
        127.0.0.1	localhost	{hostname}

        # The following lines are desirable for IPv6 capable hosts
        ::1	localhost ip6-localhost ip6-loopback
        ff02::1	ip6-allnodes
        ff02::2	ip6-allrouters
        """
    assert tasks["etc/hosts"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_persistent_interface_names(bonded_network_builder, distro, version):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/udev/rules.d/70-persistent-net.rules is generated.
    """
    builder = bonded_network_builder(distro, version)
    tasks = builder.render()

    result = """\
        # This file was automatically generated by the Equinix Metal installation environment.
        # See https://github.com/packethost/packet-networking for details.
        #
        # You can modify it, as long as you keep each rule on a single
        # line, and change only the value of the NAME= key.
        """
    result = dedent(result)

    for iface in builder.network.interfaces:
        partial = f"""
            # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
            SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{{address}}=="{iface.mac}", ATTR{{dev_id}}=="0x0", ATTR{{type}}=="1", NAME="{iface.name}"
            """
        result += dedent(partial)
    assert tasks["etc/udev/rules.d/70-persistent-net.rules"] == dedent(result)
