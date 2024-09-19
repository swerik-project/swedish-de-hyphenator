#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A python program to remove end-line hyphenations from large texts.

Author: Stian Rødven Eide
"""
from swedish_dehyphenator.config import fetch_config
from tqdm import tqdm
import argparse
import getch
import json
import os
import pickle
import re




def parsejson(jfile):
    """
    Reads a json file in utf-8 and returns its contents as a nested dictionary

    Args:
    - jfile: json file, incl path
    """
    with open(jfile, 'r', 'utf-8-sig') as jdoc:
        anfdict = json.loads(jdoc, encoding='utf-8')

    return anfdict




def savejson(jfile, path, anfdict):
    """
    Saves formatted JSON file.

    Args:
    - jfile: json file name
    - path: path to json file
    - anfdict: dict to save
    """
    with codecs.open(path + jfile, 'w','utf-8-sig') as f:
        json.dump(anfdict, f, ensure_ascii=False, indent=4)




def clean_anftext(anftext):
    """
    This function removes unwanted formatting from the text
    These remove html-tags and inline headers

    Args:
    - anftext: input text
    """
    anftext = re.sub('<p> STYLEREF.*?>',' ', anftext)
    anftext = re.sub('<.*?>',' ', anftext)
    # These remove linebreaks and redundant whitespace
    anftext = re.sub('\n',' ', anftext)
    anftext = re.sub('\r',' ', anftext)
    anftext = re.sub(' {2,}',' ', anftext)

    return anftext




def _print(s, p):
    """
    Print string or write with twdm if p is not None

    Args:
    - s: string to print
    - p: tqdm progress bar
    """
    if p is not None:
        p.write(s)
    else:
        print(s)





def file_loc_prompt(filetype):
    """
    Prompt user for a file location, if one is not set in the config.

    Args:
    - filetype: A string helper so we know what variable the program wants to write
    """
    file_loc = input(f"I don't know where to save your - {filetype} - file. Please enter a path (default: ./):\n")
    if file_loc.strip() == '':
        file_loc = "./"

    return file_loc




def _log_results(selected, autojoined, config=None):
    if config is None:
        config = {}
    if 'selected_path' not in config or config['selected_path'] is None:
        config['selected_path'] = file_loc_prompt("selected")
    with open(config['selected_path'],'wb') as f:
        pickle.dump(selected, f)
    if 'autojoined_path' not in config or config['autojoined_path'] is None:
        config['autojoined_path'] = file_loc_prompt("autojoined")
    with open(config['autojoined_path'],'wb') as f:
        pickle.dump(autojoined,f)



def ask_user(autojoined, selected, log_results, progbar=None, config=None):
    """
    Here, the user is asked what to do with an instance of
    'word- anotherword'
    (J)oin means to remove the dash and the space:
        wordanotherword
    (D)ash means to remove the space:
        word-anotherword
    (K)eep means to keep it as is:
        word- anotherword
    A single character of the above is returned.

    Args:
    - autojoined: auomatic fixes based on heuristic
    - selected: previously selected fixes
    - log_results: to log or not to log
    - progbar: a progress bar instance
    - config: a config dict
    """
    _print("Would you like to (J)oin, (D)ash or (K)eep it?", progbar)
    #TODO: cosmetic -- getch prints a new line and the progress bar wont stay on the bottom line :|
    char = getch.getch()
    char = char.lower()
    print_D = {"d":"Dashing!", "j": "Joining!", "k": "Keeping!"}
    if char in print_D:
        _print(print_D[char], progbar)
    elif char == "a":
        _print("Are you sure you want to abort? (Y/N)", progbar)
        if getch.getch().lower() == 'y':
            _print("Aborting!", progbar)
            if log_results:
                _log_results(selected, autojoined, config=config)
        else:
            ask_user(autojoined, selected, log_results, progbar=progbar, config=config)
    else:
        _print("Try again", progbar)
        ask_user(autojoined, selected, log_results, progbar=progbar, config=config)

    return char




def dehyphenate_text(_text, wf, selected, autojoined, log_results, dcounter, progbar=None, config=None):
    """
    Dehyphenate text input
    Args:
    - _text: a string to dehyphenate
    - wf: path to pickle, which is a word frequency dictionary with all words from parliamentary debates and their frequencies there: 'word': freq
    - selected: previously selected fixes
    - autojoined: auomatic fixes based on heuristic
    - log_results: to log or not to log
    - dcounter: couter of hyphenation fixes
    - progbar: progress bar instance
    - config: a config dict
    """
    _text = clean_anftext(_text)
    dashes = re.findall('\w+- \w+', _text)
    if dashes is None:
        return _text

    for dash in set(dashes):
        _print("Processing '{}' ...".format(dash), progbar)
        jdash = re.sub('- ','',dash)
        ddash = re.sub('- ','-',dash)
        if selected is not None and jdash.lower() in selected:
            _print("'{}' was selected earlier".format(jdash), progbar)
            newdash = jdash
        elif selected is not None and  ddash.lower() in selected:
            _print("'{}' was selected earlier".format(ddash), progbar)
            newdash = ddash
        elif re.match('[A-ZÅÄÖ]+-[a-zåäö]+',ddash):
            _print("Matching '[A-Z]+-[a-z]+' rule, dashing!", progbar)
            newdash = ddash
        elif re.match('[A-ZÅÄÖ][a-zåäö]+-[A-ZÅÄÖ][a-zåäö]+',ddash):
            _print("Matching '[A-Z][a-z]+-[A-Z][a-z]+' rule, dashing!", progbar)
            newdash = ddash
        elif re.match('\d+-\w+',ddash):
            _print("Matching '\d+-\w+' rule, dashing!", progbar)
            newdash = ddash
        elif re.match('icke-\w+',ddash):
            _print("Matching 'icke-\w+' rule, dashing!", progbar)
            newdash = ddash
        elif wf is not None and jdash.lower() in wf and ddash.lower() in wf:
            _print("Both '{}' and '{}' are in the word frequency list".format(jdash, ddash), progbar)
            if wf[jdash.lower()] > wf[ddash.lower()]:
                _print("'{}' is more frequent, choosing that".format(jdash), progbar)
                newdash = jdash
            elif wf[jdash.lower()] < wf[ddash.lower()]:
                _print("'{}' is more frequent, choosing that".format(ddash), progbar)
                newdash = ddash
            else:
                _print("They're equally frequent")
                tbd = ask_user(autojoined, selected, log_results, progbar=progbar, config=config)
                if tbd == 'j':
                    newdash = jdash
                elif tbd == 'd':
                    newdash = ddash
                elif tbd == 'a':
                    return
        elif wf is not None and jdash.lower() in wf:
            _print("Only '{}' was found in the word frequency list".format(jdash), progbar)
            newdash = jdash
        elif wf is not None and ddash.lower() in wf:
            _print("Only '{}' was found in the word frequency list".format(ddash), progbar)
            newdash = jdash
        else:
            _print("Neither '{}' nor '{}' are in the word frequency list".format(jdash, ddash), progbar)
            predash, postdash = ddash.split('-')
            if selected is not None and wf is not None and predash not in selected and postdash not in selected and predash.lower() not in wf:
                _print("However, neither '{}' nor '{}' seem to be words, so joining!".format(predash, postdash), progbar)
                autojoined.append(jdash)
                newdash = jdash
            else:
                tbd = ask_user(autojoined, selected, log_results, progbar=progbar, config=config)
                if tbd == 'j':
                    newdash = jdash
                elif tbd == 'd':
                    newdash = ddash
                elif tbd == 'a':
                    return
                else:
                    newdash = dash
        selected.append(newdash.lower())
        _text = re.sub(dash, newdash, _text)
        # Keeping track of how many dashes we fix
        dcounter +=1

    return _text, dcounter




def dehyphenate_anf_dict(_files, wf_anf, selected, autojoined, output_path, log_results, dcounter, fcounter, config=None):
    """
    Find dashes in anf dict text and potentially remove them.

    Args:
    - _files: list of input files prepared in `dehyphenate_from`
    - wf_anf: path to pickle, which is a word frequency dictionary with all words from parliamentary debates and their frequencies there: 'word': freq
    - selected: previously selected fixes
    - autojoined: auomatic fixes based on heuristic
    - output_path: output path
    - log_results: to log or not to log
    - dcounter: couter of hyphenation fixes
    - fcounter: file process counter
    - config: a config dict
    """
    progbar = tqdm(total=len(_files), desc="Files", position=0, leave=True)
    progbar.update(0)
    for _file in _files:
        fcounter += 1
        anfdict = parsejson(_file)
        _text, dcounter = dehyphenate_text(anfdict['anforande']['anforandetext'], wf_anf, selected, autojoined, dcounter, progbar=progbar, config=config)
        anftext_clean = _text.strip()
        anfdict['anforande']['anforandetext'] = anftext_clean
        savejson(f"{_file.split('/')[-1]}", output_path, anfdict)
    _print("We went through a total of {} dashwords!".format(dcounter), progbar)
    if log_results:
        _log_results(selected, autojoined, config=config)

    return fcounter, dcounter




def dehyphenate_txt_file(_files, wf_anf, selected, autojoined, output_path, log_results, dcounter, fcounter, config=None):
    """
    Find dashes in text files and potentially remove them.

    Args:
    - _files: list of input files prepared in `dehyphenate_from`
    - wf_anf: path to pickle, which is a word frequency dictionary with all words from parliamentary debates and their frequencies there: 'word': freq
    - selected: previously selected fixes
    - autojoined: auomatic fixes based on heuristic
    - output_path: output path
    - log_results: to log or not to log
    - dcounter: couter of hyphenation fixes
    - fcounter: file process counter
    - config: a config dict
    """
    progbar = tqdm(total=len(_files), desc="Files", position=0, leave=True)
    progbar.update(0)
    for _file in _files:
        fcounter += 1
        with open(_file, 'r') as f:
            pre_text = clean_anftext(f.read())
        _text, dcounter = dehyphenate_text(pre_text, wf_anf, selected, autojoined, dcounter, progbar=progbar, config=config)
        with open(f"{output_path}{_file.split('/')[-1]}", "w+") as o:
            o.write(_text)
        progbar.update(1)
    if log_results:
        _log_results(selected, autojoined, config=config)

    return fcounter, dcounter




def dehyphenate_from(input_path, source_type, wf_anf, selected, autojoined, output_path, log_results, dcounter, fcounter, config=None):
    """
    Deyphenate text in files.

    Args:
    - input_path: path to a directory of files to operate on
    - source_type: tyope of files in the source directory (anf_dict or txt_file)
    - wf_anf: path to pickle, which is a word frequency dictionary with all words from parliamentary debates and their frequencies there: 'word': freq
    - selected: previously selected fixes,
    - autojoined: automatic fixes based on heuristic
    - output_path: where to write output (file names will be the same as inpug files
    - log_results: to log or not to log
    - dcounter: couter of hyphenation fixes
    - fcounter: file process counter
    - config: a config dict

    """
    _fns = {
        "anf_dict": dehyphenate_anf_dict,
        "txt_file": dehyphenate_txt_file,
    }
    if os.path.isdir(input_path):
        _files = [f"{input_path}/{_}" for _ in os.listdir(input_path)]
    else:
        _files = [input_path]

    fcounter, dcounter = _fns[source_type](_files, wf_anf, selected, autojoined, output_path, log_results, dcounter, fcounter, config=config)

    return fcounter, dcounter




def dehyphenate(input_string=None,
                autojoined=None,
                selected=None,
                input_path=None,
                output_path=None,
                source_type=None,
                wf_anf=None,
                log_results=True,
                config=None):
    """
    Main dehyphenator program.

    Args:
    - input_string: a raw string to dehyphenate
    - autojoined: path to autojoined.pickle, a list of previous automatic fixes based on heuristic
    - selected: path to selected.pickle, a list of previously selected fixes
    - input_path: input path
    - output_path: output path
    - wf_anf: path to pickle, which is a word frequency dictionary with all words from parliamentary debates and their frequencies there: 'word': freq
    - log_results: bool -- save results or nah
    """
    dcounter = 0
    fcounter = 0
    try:
        with open(autojoined, 'rb') as f:
            autojoined = pickle.load(f)
    except:
        autojoined = []
    try:
        with open(selected, 'rb') as f:
            selected = pickle.load(f)
    except:
        selected = []
    try:
        with open('wf_anf.pickle', 'rb') as f:
            wf_anf = pickle.load(f)
    except:
        wf_anf = None

    if input_string is not None:
        output_string, dcounter = dehyphenate_text(input_string, wf_anf, selected, autojoined, log_results, dcounter, config=config)
        if log_results:
            _log_results(selected, autojoined, config=config)
        return output_string, dcounter, fcounter
    else:
        fcounter, dcounter = dehyphenate_from(input_path, source_type, wf_anf, selected, autojoined, output_path, log_results, dcounter, fcounter, config=config)
        return None, dcounter, fcounter



#if __name__ == '__main__':
def cli():
    """
    Run the dehypenator from the command line.
    """
    parser = argparse.ArgumentParser(description=__doc__, prog="Swedish de-hyphenator")

    subparsers = parser.add_subparsers(help="sub-command help")
    read_from = subparsers.add_parser('read_from', help="read text from file or files")
    read_from.add_argument("-i", "--input_path",
                        type=str,
                        default=None,
                        help="Input path")
    read_from.add_argument("-s", "--source-type",
                        type=str,
                        choices=["anf_dict", "txt_file"],
                        required=True,
                        help="What kind of data do you want to dehyphenate? anf_dict: reads json files of statement dictionaries from the input path. txt_file: reads data from text files. For anf_dict and string_from_file, when input path is a file, the program will process the file, if it is a directory, the files in that directory will be processed.")

    read_raw = subparsers.add_parser("raw", help="Dehyphenate raw input")
    read_raw.add_argument("input_string",
                          metavar="input_string",
                          type=str,
                          help="Input string for dehyphenating raw strings")

    parser.add_argument("-o", "--output_path",
                        type=str,
                        default="./",
                        help="Output path")
    parser.add_argument("--wf-anf",
                        type=str,
                        default=None,
                        help="a pickled word frequency dictionary with all words from parliamentary debates and their frequencies there: 'word': freq")
    parser.add_argument("--autojoined",
                        type=str,
                        default=None,
                        help="a pickle of previously autojoined entries")
    parser.add_argument("--selected",
                        type=str,
                        default=None,
                        help="a pickle of previously selected corrections")
    parser.add_argument("--log-results", type=bool, default=True)

    args = parser.parse_args()
    config, conf_loc = fetch_config()
    if args.wf_anf is None:
        args.wf_anf = config["wf_path"]
    if args.autojoined is None:
        args.autojoined = config["autojoined_path"]
    if args.selected is None:
        args.selected = config["selected_path"]

    try:
        if os.path.isdir(args.input_path) and not args.input_path.endswith("/"):
            args.input_path = f"{args.input_path}/"
    except:
        pass
    if os.path.isdir(args.output_path) and not args.output_path.endswith("/"):
        args.output_path = f"{args.output_path}/"
    output_string, d, f = dehyphenate(**vars(args))
    if output_string is None:
        print(f"{d} hyphens removed in {f} files")
    else:
        print(output_string)

