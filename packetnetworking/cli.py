import sys
import time
import json
import click
import logging
import packetnetworking

log = logging.getLogger("packetnetworking")


# pylama:ignore=C901
@click.command()
@click.option(
    "-M",
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
    "-o", "--operating-system", help="Operating System and version (ex: centos 7)"
)
@click.option(
    "-t", "--rootfs", type=click.Path(), required=True, help="Path to root filesystem"
)
@click.option(
    "--resolvers",
    envvar="PACKET_RESOLVERS",
    help=(
        "Comma separated list of resolvers to be used "
        + "(otherwise uses ones from /etc/resolv.conf)"
    ),
)
@click.option(
    "-n",
    "--max-attempts",
    default=10,
    help="Retry up to N times on failure when downloading metadata from a url",
)
@click.option("-v", "--verbose", count=True, help="Provide more detailed output")
@click.option("-q", "--quiet", is_flag=True, help="Silences all output")
def cli(
    metadata_file,
    metadata_url,
    operating_system,
    rootfs,
    resolvers,
    max_attempts,
    verbose,
    quiet,
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

    attempt = 1
    while True:
        try:
            try_run(
                metadata_file,
                metadata_url,
                operating_system,
                rootfs,
                resolvers,
                verbose,
                quiet,
            )
            break
        except Exception as exc:
            # If a metadata file has been passed, retrying won't result in a
            # different outcome.
            if metadata_file:
                raise
            if attempt == max_attempts:
                raise
            attempt += 1
            delay = 2 ** min(attempt, 7)
            log.error(
                "Caught unexpected exception ('{}'), retrying in {} seconds...".format(
                    exc, delay
                )
            )
            time.sleep(delay)


def try_run(
    metadata_file, metadata_url, operating_system, rootfs, resolvers, verbose, quiet
):
    builder = packetnetworking.Builder()
    if metadata_file:
        builder.set_metadata(json.load(metadata_file))
    else:
        builder.load_metadata(metadata_url)

    if operating_system:
        if len(operating_system.split()) != 2:
            if not quiet:
                click.echo(
                    "Operating system '{}' must include both distro and version".format(
                        operating_system
                    ),
                    file=sys.stderr,
                )
            sys.exit(20)
        os_name, os_version = operating_system.split()
        os = builder.metadata.operating_system
	if os.distro.lower() != os_name.lower() or os.version.lower() != os_version.lower():
            os.orig_distro = os.distro
            os.orig_version = os.version
            os.distro = os_name.lower()
            os.version = os_version
            log.debug(
                (
                    "Operating system mismatch. "
                    + "metadata='{os.orig_distro} {os.orig_version}', "
                    + "requested='{os.distro} {os.version}'"
                ).format(os=os)
            )

    builder.initialize()
    if resolvers:
        resolvers = [x for x in resolvers.split(",") if x.strip()]
        if resolvers:
            builder.network.resolvers = resolvers

    tasks = builder.run(rootfs)
    if not tasks:
        if not quiet:
            click.echo("No tasks processed", file=sys.stderr)
        sys.exit(30)
    if not quiet:
        print("Configuration files written to root filesystem '{}'".format(rootfs))
