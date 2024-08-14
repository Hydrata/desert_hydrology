# UAE hydrology

![Workflow Status](https://github.com/Hydrata/uae_hydrology/actions/workflows/pytest.yml/badge.svg)

The objective of this work is to create a suitable set of hyetographs representing the rainfall event of April 16-18 2024 in Dubai, UAE.

## Installation
In case you need to configure things from scratch quickly using a VM/WSL for example:
```
sudo apt update
sudo apt install -y python3 python3-pip python-is-python3
ssh-keygen -t rsa -b 4096 -C "my_email@gmail.com"
eval "$(ssh-agent -s)"
ssh-add /home/ubuntu/.ssh/my_new_github_key_name
cat /home/ubuntu/.ssh/my_new_github_key_name.pub | clip.exe
```
then paste the public key in [https://github.com/settings/ssh/new](https://github.com/settings/ssh/new)

`git clone git@github.com:Hydrata/uae_hydrology.git`

`pip install ansible`

restart your shell, then
```
cd /path/to/uae_hydrology/
ansible-playbook ./playbooks/install_grass_for_python.yaml --ask-become-pass
```
> Note if you're on Windows, using ubuntu on WSL2, you can't use the `/mnt/c/something/uae_hydrology` directory because your ubuntu user won't have write permissions. Copy the repo somewhere else like this:
`sudo cp -r /mnt/c/hydrata/uae_hydrology /home/ubuntu/uae_hydrology`

## Execution
The easiest way to run the project is to run the tests:

`python -m pytest ./tests -rsP --color=yes`

If the tests run successfully, you should have a new directory named `./output_data` with the output files saved there. The GRASS database will also be preserved in the `./database` directory, if needed for debugging.

Note, these directories are considered ephemeral and are cleaned at the start of each run.
