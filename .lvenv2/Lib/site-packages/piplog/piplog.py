import argparse
import subprocess
import os
from datetime import datetime

HISTORY_FILE = '.piplog'

def save():
    """
    Saves the current list of installed packages to the history with a timestamp.
    """
    try:
        result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True, check=True)
        packages = sorted(line.strip() for line in result.stdout.splitlines() if line.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error fetching package list: {e}")
        return

    timestamp = datetime.now().isoformat()
    version_entry = f"--- Version: {timestamp} ---\n" + "\n".join(packages) + "\n\n"

    with open(HISTORY_FILE, 'a') as f:
        f.write(version_entry)

    print(f"Saved current package list as version {timestamp}.")


def parse_history():
    """
    Parses the history file and returns a dictionary of versions with their corresponding packages.
    """
    if not os.path.exists(HISTORY_FILE):
        print("No history found. Use 'save' to create a history entry.")
        return {}

    with open(HISTORY_FILE, 'r') as f:
        content = f.read()

    versions = content.strip().split('--- Version:')
    parsed_versions = {}
    for v in versions:
        if v.strip() == '':
            continue
        lines = v.strip().split('\n')
        header = lines[0].strip()
        timestamp = header.replace('--- Version: ', '').replace(' ---', '')
        packages = set(line.strip() for line in lines[1:] if line.strip())
        parsed_versions[timestamp] = packages

    return parsed_versions


def get_current_packages():
    """
    Retrieves the current set of installed packages.
    """
    try:
        result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True, check=True)
        packages = set(line.strip() for line in result.stdout.splitlines() if line.strip())
        return packages
    except subprocess.CalledProcessError as e:
        print(f"Error fetching current packages: {e}")
        return set()


def diff(version1=None, version2=None):
    """
    Displays the differences between two specified versions or between a version and the current state.
    """
    versions = parse_history()
    if not versions:
        return

    sorted_versions = sorted(versions.keys())
    if version1 and not version2:
        if version1 not in versions:
            print(f"Version {version1} not found.")
            return
        current_packages = get_current_packages()
        target_packages = versions[version1]
        diff_added = current_packages - target_packages
        diff_removed = target_packages - current_packages
        version2 = 'current'
    elif version1 and version2:
        if version1 not in versions or version2 not in versions:
            print("One or both versions not found.")
            return
        packages1 = versions[version1]
        packages2 = versions[version2]
        diff_added = packages2 - packages1
        diff_removed = packages1 - packages2
    else:
        if len(sorted_versions) < 2:
            print("Not enough versions to compare.")
            return
        version1 = sorted_versions[-2]
        version2 = sorted_versions[-1]
        packages1 = versions[version1]
        packages2 = versions[version2]
        diff_added = packages2 - packages1
        diff_removed = packages1 - packages2

    print(f"Differences between versions '{version1}' and '{version2 if version2 else 'current'}':")
    if diff_added:
        print("\nAdded packages:")
        for pkg in sorted(diff_added):
            print(f"  + {pkg}")
    if diff_removed:
        print("\nRemoved packages:")
        for pkg in sorted(diff_removed):
            print(f"  - {pkg}")
    if not diff_added and not diff_removed:
        print("No differences found.")


def restore(version=None):
    """
    Restores the installed packages to a specified version from the history.
    """
    versions = parse_history()
    if not versions:
        return

    sorted_versions = sorted(versions.keys())
    if version and version not in versions:
        print(f"Version '{version}' not found.")
        return
    elif not version:
        # If no version is specified, restore to the latest version
        if len(sorted_versions) < 1:
            print("No versions to restore to.")
            return
        version = sorted_versions[-1]

    confirmation = input(f"Are you sure you want to restore to version '{version}'? This will delete all history entries after this version. (y/N): ")
    if confirmation.lower() != 'y':
        print("Restore canceled.")
        return

    target_packages = versions[version]
    current_packages = get_current_packages()

    # Calculate differences
    packages_to_uninstall = current_packages - target_packages
    packages_to_install = target_packages - current_packages

    if not packages_to_uninstall and not packages_to_install:
        print("No differences found between the current state and the target version. No actions needed.")
        return

    print("\nPackages to uninstall:")
    for pkg in sorted(packages_to_uninstall):
        print(f"  - {pkg}")

    print("\nPackages to install:")
    for pkg in sorted(packages_to_install):
        print(f"  + {pkg}")

    proceed = input("\nProceed with uninstalling and installing the above packages? (y/N): ")
    if proceed.lower() != 'y':
        print("Restore operation canceled.")
        return

    # Uninstall packages
    if packages_to_uninstall:
        try:
            print("\nUninstalling packages...")
            subprocess.run(['pip', 'uninstall', '-y'] + sorted(packages_to_uninstall), check=True)
            print("Uninstallation completed.")
        except subprocess.CalledProcessError as e:
            print(f"Error during uninstallation: {e}")
            return

    # Install packages
    if packages_to_install:
        try:
            print("\nInstalling packages...")
            subprocess.run(['pip', 'install'] + sorted(packages_to_install), check=True)
            print("Installation completed.")
        except subprocess.CalledProcessError as e:
            print(f"Error during installation: {e}")
            return

    # Truncate history file after the specified version
    new_history = ""
    for v in sorted_versions:
        new_history += f"--- Version: {v} ---\n"
        sorted_pkgs = sorted(versions[v])
        new_history += "\n".join(sorted_pkgs) + "\n\n"
        if v == version:
            break

    with open(HISTORY_FILE, 'w') as f:
        f.write(new_history)

    print(f"\nRestored to version '{version}'. All subsequent history entries have been deleted.")


def clear():
    """
    Clears the history file after user confirmation.
    """
    if not os.path.exists(HISTORY_FILE):
        print("No history found to clear.")
        return

    confirmation = input("Are you sure you want to clear all history? This action cannot be undone. (y/N): ")
    if confirmation.lower() == 'y':
        os.remove(HISTORY_FILE)
        print("History cleared.")
    else:
        print("Clear operation canceled.")


def pip_command(pip_args):
    """
    Executes a pip command with the provided arguments and saves a new version to the history upon success.
    """
    if not pip_args:
        print("No pip command provided.")
        return

    try:
        print(f"\nExecuting pip command: pip {' '.join(pip_args)}")
        subprocess.run(['pip'] + pip_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing pip command: {e}")
        return

    # After successful pip command, add a new history entry
    print("\nSaving new package list to history...")
    save()


def main():
    """
    Main function to parse command-line arguments and execute corresponding functions.
    """
    parser = argparse.ArgumentParser(description='piphistory: Track pip package history.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # save command
    parser_save = subparsers.add_parser('save', help='Save current package list to history')

    # diff command
    parser_diff = subparsers.add_parser('diff', help='View differences between package versions')
    parser_diff.add_argument('version1', nargs='?', default=None, help='First version to compare')
    parser_diff.add_argument('version2', nargs='?', default=None, help='Second version to compare')

    # restore command
    parser_restore = subparsers.add_parser('restore', help='Restore to a specific package version')
    parser_restore.add_argument('version', nargs='?', default=None, help='Version to restore to')

    # clear command
    parser_clear = subparsers.add_parser('clear', help='Clear the package history')

    # pip command
    parser_pip = subparsers.add_parser('pip', help='Execute a pip command and track changes')
    parser_pip.add_argument('pip_args', nargs=argparse.REMAINDER, help='Arguments for pip command')

    args = parser.parse_args()

    if args.command == 'save':
        save()
    elif args.command == 'diff':
        diff(args.version1, args.version2)
    elif args.command == 'restore':
        restore(args.version)
    elif args.command == 'clear':
        clear()
    elif args.command == 'pip':
        pip_command(args.pip_args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
