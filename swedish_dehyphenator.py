#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Stian Rødven Eide

import json
import codecs
import re
import os
import pickle
import getch

def parsejson(jfile, path):
    # Reads a json file in utf-8 and returns its
    # contents as a nested dictionary
    jdoc = codecs.open(path + jfile, 'r', 'utf-8-sig')
    jdoc = jdoc.read()
    anfdict = json.loads(jdoc, encoding='utf-8')
    return anfdict

def savejson(jfile, path, anfdict):
    with codecs.open(path + jfile, 'w','utf-8-sig') as f:
        json.dump(anfdict, f, ensure_ascii=False, indent=4)


def clean_anftext(anftext):
    # This function removes unwanted formatting from the text
    # These remove html-tags and inline headers
    anftext = re.sub('<p> STYLEREF.*?>',' ', anftext)
    anftext = re.sub('<.*?>',' ', anftext)
    # These remove linebreaks and redundant whitespace
    anftext = re.sub('\n',' ', anftext)
    anftext = re.sub('\r',' ', anftext)
    anftext = re.sub(' {2,}',' ', anftext)
    return anftext

def ask_user():
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
    """
    print("Would you like to (J)oin, (D)ash or (K)eep it?")
    char = getch.getch()
    char = char.lower()
    if char == "j":
        print("Joining!")
    elif char == "d":
        print("Dashing!")
    elif char == "k":
        print("Keeping!")
    elif char == "a":
        print("Are you sure you want to abort? (Y/N)")
        if getch.getch().lower() == 'y':
            print("Aborting!")
            with open('selected.pickle','wb') as f:
                pickle.dump(selected,f)
            with open('autojoined.pickle','wb') as f:
                pickle.dump(autojoined,f)
        else:
            ask_user()
    else:
        print("Try again")
        ask_user()
    return char

def fixbrokens(inpath,wf,outpath):
    ignorewords = ['och','eller','som','till','utan','respektive', 'såväl', 
                   'snart', 'samt', 'kontra', 'än', 'men', 'o', 'inklusive', 
                   'framför', 'liksom','og','und']
    # This counter is just to get an idea of how many files there are left to process
    counter = 0
    # This counter is for testing, to abort after a set number of dashes
    dcounter = 0
    # A list of all input files, presumed json
    filelist = os.listdir(path=inpath)
    totalfiles = len(filelist)
    # This will keep track of what manual selections have been made 
    # with regards to dashes: Joining/Dashing/Keeping
    # I should store the final list as a frequency dict
    for file in filelist:
        counter += 1
        if counter % 10000 == 0:
            print('Passed {} files of {}'.format(counter,totalfiles))
        # Getting the json data in the file as a dict
        anfdict = parsejson(file, inpath)
        # Getting the speech text from the dict
        anftext = anfdict['anforande']['anforandetext']
        # Removing tags, linebreaks and redundant whitespace
        anftext_clean = clean_anftext(anftext)
        # Find all instances of 'word- anotherword'
        dashes = re.findall('\w+- \w+', anftext_clean)
        # Filtering out those that probably should be kept
        dashes = [d for d in dashes if not d.split()[1] in ignorewords]
        if dashes:
#            print("Text before processing")
#            print(anftext_clean)
            for dash in set(dashes):
                print("Processing '{}' ...".format(dash))
                jdash = re.sub('- ','',dash)
                ddash = re.sub('- ','-',dash)
                if jdash.lower() in selected:
                    print("'{}' was selected earlier".format(jdash))
                    newdash = jdash
                elif ddash.lower() in selected:
                    print("'{}' was selected earlier".format(ddash))
                    newdash = ddash
                elif re.match('[A-ZÅÄÖ]+-[a-zåäö]+',ddash):
                    print("Matching '[A-Z]+-[a-z]+' rule, dashing!")
                    newdash = ddash
                elif re.match('[A-ZÅÄÖ][a-zåäö]+-[A-ZÅÄÖ][a-zåäö]+',ddash):
                    print("Matching '[A-Z][a-z]+-[A-Z][a-z]+' rule, dashing!")
                    newdash = ddash
                elif re.match('\d+-\w+',ddash):
                    print("Matching '\d+-\w+' rule, dashing!")
                    newdash = ddash
                elif re.match('icke-\w+',ddash):
                    print("Matching 'icke-\w+' rule, dashing!")
                    newdash = ddash
                elif jdash.lower() in wf and ddash.lower() in wf:
                    print("Both '{}' and '{}' are in the word frequency list".format(jdash, ddash))
                    if wf[jdash.lower()] > wf[ddash.lower()]:
                        print("'{}' is more frequent, choosing that".format(jdash))
                        newdash = jdash
                    elif wf[jdash.lower()] < wf[ddash.lower()]:
                        print("'{}' is more frequent, choosing that".format(ddash))
                        newdash = ddash
                    else:
                        print("They're equally frequent")
                        tbd = ask_user()
                        if tbd == 'j':
                            newdash = jdash
                        elif tbd == 'd':
                            newdash = ddash
                        elif tbd == 'a':
                            return
                elif jdash.lower() in wf:
                    print("Only '{}' was found in the word frequency list".format(jdash))
                    newdash = jdash
                elif ddash.lower() in wf:
                    print("Only '{}' was found in the word frequency list".format(ddash))
                    newdash = jdash
                else:
                    print("Neither '{}' nor '{}' are in the word frequency list".format(jdash, ddash))
                    predash, postdash = ddash.split('-')
                    if predash not in selected and postdash not in selected and predash.lower() not in wf:
                        print("However, neither '{}' nor '{}' seem to be words, so joining!".format(predash, postdash))
                        autojoined.append(jdash)
                        newdash = jdash
                    else:
                        print("We have so far processed {} of {} files".format(counter,totalfiles))
                        tbd = ask_user()
                        if tbd == 'j':
                            newdash = jdash
                        elif tbd == 'd':
                            newdash = ddash
                        elif tbd == 'a':
                            return
                        else:
                            newdash = dash
                selected.append(newdash.lower())
                anftext_clean = re.sub(dash,newdash,anftext_clean)
#            print("Text after processing")
#            print(anftext_clean)
                # Keeping track of how many dashes we fix
                dcounter +=1
        # here
        anftext_clean = anftext_clean.strip()
        anfdict['anforande']['anforandetext'] = anftext_clean
        savejson(file,outpath,anfdict)
    print("We went through a total of {} dashwords!".format(dcounter))
    with open('selected.pickle','wb') as f:
        pickle.dump(selected,f)
    with open('autojoined.pickle','wb') as f:
        pickle.dump(autojoined,f)


if __name__ == '__main__':
    inpath = "all_anf/"
    outpath = "fixed_anf/"
    try:
        with open('autojoined.pickle', 'rb') as f:
            autojoined = pickle.load(f)
    except FileNotFoundError:
        autojoined = []
    try:
        with open('selected.pickle', 'rb') as f:
            selected = pickle.load(f)
    except FileNotFoundError:
        selected = []
    # wf_anf.pickle is a word frequency dictionary with all words from parliamentary
    # debates and their frequencies there: 'word': freq
    with open('wf_anf.pickle', 'rb') as f:
        wf_anf = pickle.load(f)
    fixbrokens(inpath,wf_anf,outpath)
