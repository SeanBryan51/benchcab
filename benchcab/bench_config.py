import yaml
from pathlib import Path


def check_config(config: dict):
    required_keys = ['use_branches', 'project', 'user', 'modules']
    if any([key not in config for key in required_keys]):
        raise ValueError(
            "The config file does not list all required entries. "
            "Those are 'use_branches', 'project', 'user', 'modules'"
        )

    if len(config['use_branches']) != 2:
        raise ValueError("You need to list 2 branches in 'use_branches'")

    if any([branch_name not in config for branch_name in config['use_branches']]):
        raise ValueError(
            "At least one of the first 2 aliases listed in 'use_branches' is"
            "not an entry in the config file to define a CABLE branch."
        )

    for branch_name in config['use_branches']:
        branch_config = config[branch_name]
        required_keys = ["name", "trunk", "share_branch"]
        if any([key not in branch_config for key in required_keys]):
            raise ValueError(
                f"The '{branch_name}' does not list all required "
                "entries. Those are 'name', 'trunk', 'share_branch'."
            )
        if type(branch_config["name"]) is not str:
            raise TypeError(
                f"The 'name' field in '{branch_name}' must be a "
                "string."
            )
        # the "revision" key is optional
        if "revision" in branch_config and type(branch_config["revision"]) is not int:
            raise TypeError(
                f"The 'revision' field in '{branch_name}' must be an "
                "integer."
            )
        if type(branch_config["trunk"]) is not bool:
            raise TypeError(
                f"The 'trunk' field in '{branch_name}' must be a "
                "boolean."
            )
        if type(branch_config["share_branch"]) is not bool:
            raise TypeError(
                f"The 'share_branch' field in '{branch_name}' must be a "
                "boolean."
            )


def read_config(config_path: str) -> dict:
    with open(Path(config_path), "r") as file:
        config = yaml.safe_load(file)

    check_config(config)

    # Add "revision" to each branch description if not provided with default value -1, i.e. HEAD of branch
    for branch in config['use_branches']:
        config[branch].setdefault('revision', -1)

    # Add a "met_subset" key set to empty list if not found in config.yaml file.
    config.setdefault("met_subset", [])

    return config
