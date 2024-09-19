#!/usr/bin/env python3
"""
Set configuration options for swedish_dehyphenator.
"""
import argparse, json, os, sys



def fetch_config():
    """
    Fetch the config (dict) and config location (str)
    """
    try:
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/config-loc.txt", 'r') as loc:
            config_loc = loc.read().strip()
    except:
        print("It seems like there's no config file. Run with `init` to create one.")
        sys.exit()
    else:
        with open(config_loc, 'r') as c:
            config = json.load(c)
    return config, config_loc




def _fetch_defaults():
    """
    Return dict of default config values.
    """
    return {
            "config_path":"~/.config/swedish_dehyphenator/config.json",
            "wf_path": "~/.config/swedish_dehyphenator/wf.json",
            "autojoined_path": "~/.config/swedish_dehyphenator/autojoined.pickle",
            "selected_path": "~/.config/swedish_dehyphenator/selected.pickle",
        }




def init(args):
    """
    Initiate a config file.

    Args:
    - args: dict of values
        - config_path: path to config file. default `~/.config/swedish_dehyphenator/config.json`
        - wf_path: path to word frequency json file. default `~/.config/swedish_dehyphenator/wf.json`
        - autojoined_path: path to previoiusly autojoined words. default `~/.config/swedish_dehyphenator/autojoined.pickle`
        - selected_path: path to previously selected corrections. default `~/.config/swedish_dehyphenator/autojoined.pickle`
    """
    to_write = _fetch_defaults()
    for k, v in args.items():
        if v is not None:
            to_write[k] = v
    for k, v in to_write.items():
        if v.startswith("~"):
            to_write[k] = os.path.expanduser(v)
    _path = to_write["config_path"]
    del to_write["config_path"]
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/config-loc.txt", "w+") as l:
        l.write(_path)
    os.makedirs(os.path.dirname(_path), exist_ok=True)
    with open(_path, "w+") as c:
        json.dump(to_write, c, indent=4, ensure_ascii=False)




def show_opts(args):
    """
    Print config dict

    Args:
    - args: dict of values
        - config_path: path to config file. default `~/.config/swedish_dehyphenator/config.json`
        - wf_path: path to word frequency json file. default `~/.config/swedish_dehyphenator/wf.json`
        - autojoined_path: path to previoiusly autojoined words. default `~/.config/swedish_dehyphenator/autojoined.pickle`
        - selected_path: path to previously selected corrections. default `~/.config/swedish_dehyphenator/autojoined.pickle`
    """
    config, loc = fetch_config()
    print("\nConfig file located at:", loc, "\n")
    for k, v in config.items():
        if k != "program":
            print(f"  {k:<20}: {v}")
    print("")




def edit(args):
    """
    Edit config dict. Unset keys, or keys set to None are ignored.

    Args:
    - args: dict of values
        - config_path: path to config file. default `~/.config/swedish_dehyphenator/config.json`
        - wf_path: path to word frequency json file. default `~/.config/swedish_dehyphenator/wf.json`
        - autojoined_path: path to previoiusly autojoined words. default `~/.config/swedish_dehyphenator/autojoined.pickle`
        - selected_path: path to previously selected corrections. default `~/.config/swedish_dehyphenator/autojoined.pickle`
    """
    config, _path = fetch_config()
    for k, v in args.items():
        if k not in ["program", "config_path"]:
            if v is not None:
                config[k] = os.path.abspath(v)
    with open(_path, "w+") as c:
        json.dump(config, c, indent=4, ensure_ascii=False)
    print("\nedit successful!\n")
    show_opts(None)



#if __name__ == '__main__':
def cli():
    programs = {
            "init": init,
            "edit": edit,
            "show_opts": show_opts,
        }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", choices=["init", "edit", "show_opts"], help="What program do you want to run?")
    parser.add_argument("--config-path", default=None, help="Path to config file")
    parser.add_argument("--wf-path", default=None, help="Path to word frequency json file")
    parser.add_argument("--autojoined-path", default=None, help="Path to autojoined pickle")
    parser.add_argument("--selected-path", default=None, help="Path to selected pickle")
    args = parser.parse_args()
    programs[args.program]({**vars(args)})
