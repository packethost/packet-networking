import sys
import json
import click
import logging
import packetnetworking

log = logging.getLogger("packetnetworking")

# pylama:ignore=C901
@click.command()
@click.option(
    "--metadata-file",
    type=click.File(),
    help="Load metadata from a file rather than a URL",
)
@click.option(
    "--metadata-url",
    envvar="PACKET_METADATA_URL",
    default="http://metadata.packet.net/metadata",
    help="URL to download metadata from",
)
@click.option(
    "-o",
    "--operating-system",
    required=True,
    help="Operating System and version (ex: centos 7)",
)
@click.option(
    "--rootfs", type=click.Path(), required=True, help="Path to root filesystem"
)
@click.option(
    "--resolvers",
    envvar="PACKET_RESOLVERS",
    help=(
        "Comma separated list of resolvers to be used "
        + "(otherwise uses ones from /etc/resolv.conf)"
    ),
)
@click.option("-v", "--verbose", count=True, help="Provide more detailed output")
@click.option("-q", "--quiet", is_flag=True, help="Silences all output")
def cli(
    metadata_file, metadata_url, operating_system, rootfs, resolvers, verbose, quiet
):
    level = logging.WARNING
    if verbose:
        valid_levels = [logging.INFO, logging.DEBUG]
        try:
            level = valid_levels[verbose - 1]
            # Ignore urllib3 DEBUG messages
            urllib3_log = logging.getLogger("urllib3")
            urllib3_log.setLevel(logging.WARNING)
        except IndexError:
            # If 3 or more 'v', enable debug, and don't ignore urllib3
            level = logging.DEBUG
    if not quiet:
        logging.basicConfig(level=level)

    if not (metadata_file or metadata_url):
        if not quiet:
            print(
                "--metadata-file or --metadata-url must be specified", file=sys.stderr
            )
        click.exit(10)

    if metadata_file and metadata_url:
        log.debug(
            "Metadata file '{}' specified, preferring over metadata url.".format(
                metadata_file.name
            )
        )
    if len(operating_system.split()) != 2:
        if not quiet:
            click.fail(
                "Operating system '{}' must include both distro and version".format(
                    operating_system
                ),
                file=sys.stderr,
            )
        click.exit(20)

    builder = packetnetworking.Builder()
    if metadata_file:
        builder.set_metadata(json.load(metadata_file))
    else:
        builder.load_metadata(metadata_url)
    builder.initialize()
    if resolvers:
        resolvers = [x for x in resolvers.split(",") if x.strip()]
        if resolvers:
            builder.network.resolvers = resolvers

    builder.run(operating_system, rootfs)
    if not quiet:
        print("Configuration files written to root filesystem '{}'".format(rootfs))
