#!/usr/bin/env python
import os
import sys

import envdir

if __name__ == "__main__":

    # Read environment variables from the files in the directory "./.env/".
    current_folder = os.path.dirname(os.path.abspath(__file__))
    envdir_folder = os.path.join(current_folder, ".env")
    if os.path.exists(envdir_folder):
        envdir.open(envdir_folder)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    os.environ.setdefault('DJANGO_CONFIGURATION', 'Base')

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)
