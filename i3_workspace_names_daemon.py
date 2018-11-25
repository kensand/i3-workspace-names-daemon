#!/usr/bin/env python3
"""Dynamically update i3wm workspace names based on running applications in each and optionally define an icon to show instead."""

import json
import os.path
import argparse
import i3ipc
from fa_icons import icons

I3_CONFIG_PATHS = (os.path.expanduser("~/.i3"), os.path.expanduser("~/.config/i3"))

DEFAULT_APP_ICON_CONFIG = {
    "chromium-browser": "chrome",
    "firefox": "firefox",
    "x-terminal-emulator": "terminal",
    "thunderbird": "envelope",
    "jetbrains-idea-ce": "edit",
    "nautilus": "folder-open",
    "clementine": "music",
    "vlc": "play",
    "signal": "comment"
}


def build_rename(i3, app_icons):
    """Build rename callback function to pass to i3ipc.

    Parameters
    ----------
    i3: `i3ipc.i3ipc.Connection`
    app_icons: `dict[str, str]`
        Index of application-name (from i3) to icon-name (in font-awesome gallery).

    Returns
    -------
    func
        The rename callback.
    """
    def get_icon_or_name(leaf):
        window_class = leaf.window_class.lower()
        if window_class in app_icons and app_icons[window_class] in icons:
            return icons[app_icons[window_class]]
        else:
            return window_class.lower()

    def rename(i3, e):
        for workspace in i3.get_tree().workspaces():
            names = [get_icon_or_name(leaf)
                     for leaf in workspace.leaves()]
            names = "|".join(names)
            i3.command('rename workspace "{}" to "{}: {}"'.format(workspace.name, workspace.num, names))
    return rename


def _get_i3_dir():
    # standard i3-config directories
    for path in I3_CONFIG_PATHS:
        if os.path.isdir(path):
            return path
    raise SystemExit("Could not find i3 config directory! Expected one of {} to be present".format(I3_CONFIG_PATHS))


def _get_app_icons(config_path=None):
    """Get app-icon mapping from config file or use defaults.

    Parameters
    ----------
    config_path: `str|None`
        Path to app-icon config file.

    Returns
    -------
    dict[str,str]
        Index of application-name (from i3) to icon-name (in font-awesome gallery).

    Raises
    ------
    json.decoder.JSONDecodeError
        When app-icon config file is not in JSON format.

    SystemExit
        When `config_path is not None` and there is not a file available at tht path.
        When ~/.i3 or ~/.config/i3 is not a directory (ie. i3 is not installed).

    Notes
    -----
    If config_path is None then the locations ~/.i3/app-icons.json and ~/.config/i3/app-icons.json will also be used if available. If they are also not available then `DEFAULT_APP_ICON_CONFIG` will be used.
    """

    if config_path:
        if not os.path.isfile(config_path):
            raise SystemExit("Specified app-icon config path '{}' does not exist".format(config_path))
    else:
        config_path = os.path.join(_get_i3_dir(), "app-icons.json")

    if os.path.isfile(config_path):
        with open(config_path) as f:
            app_icons = json.load(f)
        # normalise app-names to lower
        return {k.lower(): v for k, v in app_icons.items()}
    else:
        print('Using default app-icon config {}'.format(DEFAULT_APP_ICON_CONFIG))
        return dict(DEFAULT_APP_ICON_CONFIG)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-config-path",
                        help="Path to file that maps applications to icons in json format. Defaults to ~/.i3/app-icons.json or ~/.config/i3/app-icons.json or hard-coded list if they are not available.",
                        required=False)
    args = parser.parse_args()

    app_icons = _get_app_icons(args.config_path)

    # check for missing icons
    for app, icon_name in app_icons.items():
        if not icon_name in icons:
            print("Specified icon '{}' for app '{}' does not exist!")
    # build i3-connection
    i3 = i3ipc.Connection()

    rename = build_rename(i3, app_icons)
    for case in ['window::move', 'window::new', 'window::title', 'window::close']:
        i3.on(case, rename)
    i3.main()


if __name__ == '__main__':
    main()