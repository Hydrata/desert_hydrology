# UAE hydrology

![Workflow Status](https://github.com/Hydrata/uae_hydrology/actions/workflows/pytest.yml/badge.svg)

The objective of this work is to create a suitable set of hyetographs representing the rainfall event of April 16-18 2024 in Dubai, UAE.

## Installation



```
git clone git@github.com:Hydrata/uae_hydrology.git
pip install ansible
ansible-playbook ./playbooks/install_grass_for_python.yaml
```


## Execution
The easiest way to run the project is to run the tests:

`python -m pytest ./tests -rsP --color=yes`

If they run successfully, you should have a new directory named `./output_data` with the output files saved there. The GRASS database will also be preserved in the `./database` directory, if needed for debugging.

Note, these directories are considered ephemeral and are cleaned at the start of each run.