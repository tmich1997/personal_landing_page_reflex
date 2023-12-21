"""Building the app and initializing all prerequisites."""

from __future__ import annotations

import difflib
import os
import re
import subprocess
import sys
import tempfile

from reflex_cli import constants
from reflex_cli.utils import console


def check_requirements():
    """Check if the requirements.txt needs update based on current environment.
    Throw warnings if too many installed or unused (based on imports) packages in
    the local environment.
    """
    # Run the command and get the output into a temporary requirements.txt file
    tmp_dir = tempfile.mkdtemp()

    requirements_by_pipreqs_txt = f"{tmp_dir}/requirements_by_pipreqs.txt"
    pipreqs_command = [
        "pipreqs",
        # By default, it runs in the current directory
        "--use-local",
        "--savepath",  # Save the file instead of printing to stdout. The print option outputs debug info not sure how to disable.
        requirements_by_pipreqs_txt,
    ]
    console.debug(
        f"Running command to generate requirements using pipreqs to see how many packages are actually used: {pipreqs_command}"
    )
    num_used_packages = None
    try:
        subprocess.run(
            pipreqs_command,
            capture_output=True,
            text=True,
            check=True,
        )
        with open(requirements_by_pipreqs_txt, "r") as f:
            num_used_packages = sum(1 for _ in f)
        console.debug(f"Number of used packages: {num_used_packages}")
        # Clean up the temporary requirements.txt files
        os.remove(requirements_by_pipreqs_txt)
    except subprocess.CalledProcessError as cpe:
        # Only need to log this
        console.debug(f"Unable to run pipreqs util in the subprocess: {cpe}")
    except OSError as ose:
        console.debug(
            f"Unable to interact with pipreqs generated temporary requirements.txt: {ose}"
        )

    # Run the pipdeptree command and get the output
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pipdeptree", "--warn", "silence"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as cpe:
        console.debug(f"Unable to run pipdeptree util in subprocess: {cpe}")
        console.warn(
            "Unable to detect installed packages in your environment. Please make sure your requirements.txt is up to date."
        )
        return

    # Filter the output lines using a regular expression
    lines = result.stdout.split("\n")
    new_requirements_lines = []
    for line in lines:
        if re.match(r"^\w+", line):
            new_requirements_lines.append(f"{line}\n")

    current_requirements_lines = ""
    if os.path.exists(constants.RequirementsTxt.FILE):
        with open(constants.RequirementsTxt.FILE, "r") as f:
            current_requirements_lines = list(f)
            console.debug("Current requirements.txt:")
            console.debug("".join(current_requirements_lines))

    # Show the differences of current and the newly generated requirements.txt
    diff_content = "".join(
        difflib.unified_diff(
            current_requirements_lines,
            new_requirements_lines,
            fromfile="requirements.txt",
            tofile="new_requirements.txt",
        )
    )

    if (
        num_used_packages is not None
        and (
            estimated_unused_num_packages := len(new_requirements_lines)
            - num_used_packages
        )
        >= constants.RequirementsTxt.UNUSED_WARN_THRESHOLD
    ):
        console.warn(
            f"Estimated {estimated_unused_num_packages} packages not used. Please make sure your environment is clean."
        )
    if not diff_content:
        console.info("No updates required for the requirements.txt.")
        return

    if not current_requirements_lines:
        console.info("It seems like there's no requirements.txt in your project.")
    else:
        console.info("The requirements.txt may need to be updated.")

    console.print(diff_content)

    user_choice = console.ask(
        "Would you like to update requirements.txt based on the changes above?",
        choices=["y", "n"],
    )
    if user_choice != "y":
        console.warn("Please update requirements.txt manually if needed.")
        # Not exit here since the newly generated requirements.txt is necessarily correct
        # i.e., user enters `n` to override and proceed to deploy
        return

    # Write the filtered lines to requirements.txt
    try:
        with open(constants.RequirementsTxt.FILE, "w") as f:
            f.writelines(new_requirements_lines)
            console.info("requirements.txt updated.")
    except OSError:
        console.error(
            f"Unable to write to {constants.RequirementsTxt.FILE}. Please manually update it."
        )
        sys.exit(1)
