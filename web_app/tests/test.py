import os
import platform
from zipfile import ZipFile, ZIP_DEFLATED

import regex

jobs = {
    "1": 1,
    "2": 2
}


def zip_yaml_file():
    result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/web_app/query_app/defoe_results/uris_keysearch.yml"
    # Get the directory and filename of the YAML file
    yaml_dir, yaml_filename = os.path.split(result_file_path)

    # Create a new zip file in the same directory as the YAML file
    zip_filename = os.path.join(yaml_dir, "newname.zip")
    with ZipFile(zip_filename, 'w', ZIP_DEFLATED) as zip_file:
        # Add the YAML file to the zip file
        zip_file.write(result_file_path, arcname=os.path.basename(result_file_path))


def os_type_auto_check():
    # Get platform information
    platform_name = platform.system() + " " + platform.release() + " " + platform.machine()
    print(platform_name)
    if regex.match("Darwin?1[012345]*", platform_name):
        return "sys-i386-snow-leopard"

    if regex.match("Darwin?1[6789]*", platform_name):
        return "sys-x86-64-sierra"

    if regex.match("Darwin?2*", platform_name):
        return "sys-x86-64-sierra"

    if regex.match("Linux*x86_64*", platform_name):
        return "sys-x86-64-el7"

    return None


if __name__ == '__main__':
    print(os_type_auto_check())
