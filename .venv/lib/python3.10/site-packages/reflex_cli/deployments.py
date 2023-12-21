"""The Hosting CLI deployments sub-commands."""
import asyncio
import json

import typer
from tabulate import tabulate

from reflex_cli import constants
from reflex_cli.utils import console

deployments_cli = typer.Typer()


@deployments_cli.command(name="list")
def list_deployments(
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """List all the hosted deployments of the authenticated user.

    Args:
        loglevel: The log level to use.
        as_json: Whether to output the result in json format.

    Raises:
        Exit: If the command fails.
    """
    from reflex_cli.utils import hosting

    console.set_log_level(loglevel)
    try:
        deployments = hosting.list_deployments()
    except Exception as ex:
        console.error(f"Unable to list deployments")
        raise typer.Exit(1) from ex

    if as_json:
        console.print(json.dumps(deployments))
        return
    if deployments:
        headers = list(deployments[0].keys())
        table = [list(deployment.values()) for deployment in deployments]
        console.print(tabulate(table, headers=headers))
    else:
        # If returned empty list, print the empty
        console.print(str(deployments))


@deployments_cli.command(name="delete")
def delete_deployment(
    key: str = typer.Argument(..., help="The name of the deployment."),
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Delete a hosted instance.

    Args:
        key: The name of the deployment.
        loglevel: The log level to use.

    Raises:
        Exit: If the command fails.
    """
    from reflex_cli.utils import hosting

    console.set_log_level(loglevel)

    try:
        hosting.delete_deployment(key)
    except Exception as ex:
        console.error(f"Unable to delete deployment")
        raise typer.Exit(1) from ex
    console.print(f"Successfully deleted [ {key} ].")


@deployments_cli.command(name="status")
def get_deployment_status(
    key: str = typer.Argument(..., help="The name of the deployment."),
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Check the status of a deployment.

    Args:
        key: The name of the deployment.
        loglevel: The log level to use.

    Raises:
        Exit: If the command fails.
    """
    from reflex_cli.utils import hosting

    console.set_log_level(loglevel)

    try:
        console.print(f"Getting status for [ {key} ] ...\n")
        status = hosting.get_deployment_status(key)

        # TODO: refactor all these tabulate calls
        status.backend.updated_at = hosting.convert_to_local_time_str(
            status.backend.updated_at or "N/A"
        )
        backend_status = status.backend.dict(exclude_none=True)
        headers = list(backend_status.keys())
        table = list(backend_status.values())
        console.print(tabulate([table], headers=headers))
        # Add a new line in console
        console.print("\n")
        status.frontend.updated_at = hosting.convert_to_local_time_str(
            status.frontend.updated_at or "N/A"
        )
        frontend_status = status.frontend.dict(exclude_none=True)
        headers = list(frontend_status.keys())
        table = list(frontend_status.values())
        console.print(tabulate([table], headers=headers))
    except Exception as ex:
        console.error(f"Unable to get deployment status")
        raise typer.Exit(1) from ex


@deployments_cli.command(name="logs")
def get_deployment_logs(
    key: str = typer.Argument(..., help="The name of the deployment."),
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Get the logs for a deployment.

    Args:
        key: The name of the deployment.
        loglevel: The log level to use.

    Raises:
        Exit: If the command fails.
    """
    from reflex_cli.utils import hosting

    console.set_log_level(loglevel)
    console.print("Note: there is a few seconds delay for logs to be available.")
    try:
        asyncio.get_event_loop().run_until_complete(hosting.get_logs(key))
    except Exception as ex:
        console.error(f"Unable to get deployment logs")
        raise typer.Exit(1) from ex


@deployments_cli.command(name="build-logs")
def get_deployment_build_logs(
    key: str = typer.Argument(..., help="The name of the deployment."),
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
):
    """Get the build logs for a deployment.

    Args:
        key: The name of the deployment.
        loglevel: The log level to use.

    Raises:
        Exit: If the command fails.

    """
    from reflex_cli.utils import hosting

    console.set_log_level(loglevel)

    console.print("Note: there is a few seconds delay for logs to be available.")
    try:
        # TODO: we need to find a way not to fetch logs
        # that match the deployed app name but not previously of a different owner
        # This should not happen often
        asyncio.run(hosting.get_logs(key, log_type=hosting.LogType.BUILD_LOG))
    except Exception as ex:
        console.error(f"Unable to get deployment logs")
        raise typer.Exit(1) from ex


@deployments_cli.command(name="regions")
def get_deployment_regions(
    loglevel: constants.LogLevel = typer.Option(
        constants.LogLevel.INFO, help="The log level to use."
    ),
    as_json: bool = typer.Option(
        False, "-j", "--json", help="Whether to output the result in json format."
    ),
):
    """List all the regions of the hosting service.

    Args:
        loglevel: The log level to use.
        as_json: Whether to output the result in json format.
    """
    from reflex_cli.utils import hosting

    console.set_log_level(loglevel)

    list_regions_info = hosting.get_regions()
    if as_json:
        console.print(json.dumps(list_regions_info))
        return
    if list_regions_info:
        headers = list(list_regions_info[0].keys())
        table = [list(deployment.values()) for deployment in list_regions_info]
        console.print(tabulate(table, headers=headers))
