import os
import six
import sys
import json
import pickle
import random
import argparse
import numpy as np
import topicvectors as similarity
import speech_recognition as sr



DEFAULTNAMES = {
    "$A$": "Alfred",
    "B": "Beatrice",
    "A-1": "Frank",
    "B-1": "Elizabeth",
    "A-2": "Nathaniel",
    "B-2": "Mia",
    "A-3": "Owen",
    "B-3": "Ruby",
    "A-4": "Noah",
    "B-4": "Stephanie",
    "A-5": "Thomas",
    "A-5a": "Zachary",
    "A-5b": "Seth",
    "A-5c": "Gabriel",
    "B-5": "Ariana",
    "A-6": "Garrett",
    "A-7": "Henry",
    "B-7": "Eva",
    "A-8": "Ivan",
    "B-8": "Laura",
    "A-9": "Leonardo",
    "F-A": "Brandon",
    "M-A": "Camila",
    "F-B": "Kevin",
    "M-B": "Makayla",
    "SR-A": "Kathy",
    "D-A": "Amelia",
    "SN-A": "Marco",
    "X": "Doom Orb",
    "AX": "Leonardo di ser Piero da Vinci",
    "AUX": "Irma",
    "D-A": "Carol",
    "BX": "Linda",
    "SN": "Juan",
    "CH": "Joseph",
    "BR-B": "Brian"
}

HINTCHOICES = 5

def fst(x):
    (a,b,c) = x
    return a
    
def snd(x):
    (a,b,c) = x
    return b
    
def trd(x):
    (a,b,c) = x
    return c
    
def to_np(x):
    vec = trd(x)
    if vec is None:
        return vec
    return np.array(vec)
    
def fix_hint(text):
    result = []
    for l in text:
        if l.isupper():
            result.append(" ")
        result.append(l)
    return "".join(result)

def wordset(text):
    def isal(c):
        return c.isalpha() or c.isspace()
    def islong(w):
        return len(w) > 3
    return set(filter(islong, "".join(filter(isal, text.lower())).split()))

class Storyteller(object):
    def __init__(self, story, hints, plottomodel, hintmodel, names):
        self.state = story
        self.trace = []
        self.hints = hints
        self.hinttexts = list(map(snd, self.hints))
        self.plottomodel = plottomodel
        self.hintvectors = list(map(to_np, self.hints))
        if not self.hintvectors or self.hintvectors is None:
            self.hintvectors = similarity.preprocess(hintmodel, self.hinttexts)
        self.hintmodel = hintmodel
        self.names = names

    def is_active(self):
        return self.state["children"]

    def get_text(self):
        return fix_names(self.state["text"], self.names)

    def next_beat(self, cue="", related=False):
        options = self.state["children"]
        if not cue:
            if related:
                cue = self.get_text()
            else:
                self.trace.append(self.state)
                self.state = random.choice(options)
                return
        (next,index) = similarity.closest(self.plottomodel, cue, [o["text"] for o in options])
        self.trace.append(self.state)
        self.state = options[index]

    def get_hint(self, cue=""):
        if not cue:
            cue = self.get_text()
        #print("get hint for '" + cue + "'")
        closest = similarity.closestn_v(self.hintmodel, cue, self.hintvectors, n=HINTCHOICES)
        context = wordset(self.get_text())

        def exclude_overlaps(h):
            (index,hint) = h
            hinttext = fix_hint(self.hints[index][0])
            words = wordset(hinttext)
            if words.intersection(context):
                return False
            return True

        closest = list(filter(exclude_overlaps, closest))
        (index,hint) = random.choice(closest)
        hinttext = fix_hint(self.hints[index][0])
        self.trace.append(hinttext)
        return hinttext

def get_json(fname):
    f = open(fname, "r")
    result = json.load(f)
    f.close()
    return result
    
def get_pickle(fname):
    f = open(fname, "rb")
    result = pickle.load(f)
    f.close()
    return result
    
def extract_items(chain):
    result = []
    for h in chain["states"]:
        vec = None
        if "vec" in chain["states"][h][0]:
            vec = chain["states"][h][0]["vec"]
        result.append((h,chain["states"][h][0]["text"],vec))
    return result
    
def fix_names(text, names):
    result = []
    for token in text.split():
        word = token.strip(".,;")
        suffix = token[len(word):]
        if word.endswith("'s"):
            suffix = "'s" + suffix
            word = word[:-2]
        #print(word)
        if word in names:
            result.append(names[word]+suffix)
        else:
            result.append(token)
    return " ".join(result)
    

    
# Default to no speech output
SPEECHOUTPUT = False
# which word is used to "wake" the storyteller
KEYWORD = "director" 
    
def say(text):
    cleantext = text.replace('"', "").replace("'", "").replace("`", "").replace(";", "")
    if SPEECHOUTPUT:
        print("Saying: %s"%(cleantext))
        os.system("say %s"%(cleantext))
    else:
        print(cleantext)

def main(storyf, hintf, hintmodelf, plottomodelf, speechoutput="", namef="", 
         listnames=False, log=None, auto=False, speechinput=False, keyword=False):
    """Main storyteller function. """
    global SPEECHOUTPUT
    if listnames:
        print("Default name mapping:")
        for n in DEFAULTNAMES:
            print(n, "is mapped to", DEFAULTNAMES[n])
        return
    if speechoutput:
        print('Speech Output Enabled')
        SPEECHOUTPUT = True
    else:
        print('Speech Output Disabled')
    story = get_json(storyf)
    hintsj = get_json(hintf)
    hintmodel = get_pickle(hintmodelf)
    plottomodel = get_pickle(plottomodelf)
    names = DEFAULTNAMES
    if namef:
        names = get_json(namef)
    hints = extract_items(hintsj)
    teller = Storyteller(story, hints, plottomodel, hintmodel, names)
    kws = [("next", 1), ("related", 1), ("quit", 1), ("hint", 1), ("help", 1)]
    text = teller.get_text()
    say(text)
    if log:
        current = {}
        logged_story = {"text": text, "children": [current]}
        parent = logged_story

    # build recognizer, tune microphone
    r = sr.Recognizer()
    m = sr.Microphone()
    with m as source:
        # we only need to calibrate once, before we start listening
        r.adjust_for_ambient_noise(source) 

    while teller.is_active():
        try:
            if auto:
                cmd = "next"
            elif speechinput or keyword:
                # obtain audio from the microphone
                gotcommand = False 
                while not gotcommand:    
                    with m as source:
                        print("Say something!")
                        audio = r.listen(source)
                        print('captured audio object: ', audio)
                        if keyword:
                            kws.append((KEYWORD, 1))
                        try:
                            x = r.recognize_sphinx(audio, keyword_entries=kws)
                            print('x', x)
                            cmd = x.split()
                            kw = True
                            if keyword:
                                kw = cmd[0] == KEYWORD
                                cmd = cmd[1:]
                            if kw and len(cmd) == 1:
                                gotcommand = True
                        except Exception as error:
                            print('error: ', error)
                            pass
                
            else:
                cmd = six.moves.input("Command? ")
                print('input cmd received:', cmd)
                if cmd:
                    cmd = cmd.split()
            if not cmd:
                cmd = "?"
            if cmd[0] in ["n", "next"]:
                teller.next_beat(" ".join(cmd[1:]))
                text = teller.get_text()
                say(text)
                if log:
                    current["text"] = text
                    current["children"] = [{}]
                    parent = current
                    current = current["children"][0]
            elif cmd[0] in ["r", "related"]:
                teller.next_beat(" ".join(cmd[1:]), True)
                text = teller.get_text()
                say(text)
                if log:
                    current["text"] = text
                    current["children"] = [{}]
                    parent = current
                    current = current["children"][0]
            elif cmd[0] in ["h", "hint"]:
                text = teller.get_hint(" ".join(cmd[1:]))
                say(text)
                if log: 
                    current["text"] = text
                    current["children"] = [{}]
                    parent = current
                    current = current["children"][0]
            elif cmd[0] in ["q", "quit"]:
                sys.exit(0)
            elif cmd[0] in ["?", "help"]:
                print("Valid commands: next [<cue>] or hint [<cue>] or quit")
                print("If no cue for `next` is given, a random next beat will be produced")
                print("If no cue for `hint` is given, the hint matching the current beat's text most closely will be given")
        except (SyntaxError, IndexError) as e:
            print(e)
            print("Invalid input.")
    try:
        if auto:
            cmd = "next"
        elif speechinput or keyword:
            # obtain audio from the microphone
            gotcommand = False
            while not gotcommand:
                with m as source:
                    print("Say something!")
                    audio = r.listen(source)
                try:
                    kws = [("next", 1), ("related", 1), ("quit", 1), ("hint", 1)]
                    if keyword:
                        kws.append((KEYWORD, 1))
                    x = r.recognize_sphinx(audio, keyword_entries=kws)
                    tokens = x.split()
                    kw = True
                    if keyword:
                        kw = tokens[0] == KEYWORD
                        tokens = tokens[1:]
                    if kw and len(tokens) == 1:
                        cmd = tokens[0]
                        gotcommand = True
                except Exception as error:
                    print('error: ', error)
                    pass
        else:
            cmd = six.moves.input("Finish? ").split()
    except SyntaxError as e:
        pass
    say("The End.")
    if log:
        if parent:
            parent["children"] = []
        logf = open(log, "w")
        json.dump(logged_story, logf, indent=4)
        logf.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='Tell a story given as tree, depending on actor input'
        )
    parser.add_argument('storytree', 
        help='A JSON file describing a story tree')
    parser.add_argument('hintfile', 
        help='A JSON file containing possible hints for actors')
    parser.add_argument('hintmodel', 
        help='A trained paragraph vector model to find matches for hints')
    parser.add_argument('plotmodel', 
        help='A trained paragraph vector model to find matches for story beats')
    parser.add_argument('-s', '--say', 
        help='Produce speech output instead of printing to the console', 
        action="store_true", default=False, dest="say")
    parser.add_argument('-n', '--names',
        help=('A JSON file containing actor-name mappings. ' +
              'If not provided, a set of default names will be used'),
        action="store", default=None, dest="names")
    parser.add_argument('-i', '--list', '--list-names', 
        help='List the default name mapping', 
        action="store_true", default=False, dest="listnames")
    parser.add_argument('-l', '--log', 
        help='Store log of story in JSON file', 
        action="store", default=None, dest="log")
    parser.add_argument('-a', '--auto', 
        help='Automaticallz proceed to next beat', 
        action="store_true", default=False, dest="auto")
    parser.add_argument('-p', '--speech', 
        help='Use speech input', action="store_true", 
        default=False, dest="speech")
    parser.add_argument('-k', '--kw', 
        help="Use keyword 'director' to activate speech input", 
        action="store_true", default=False, dest="kw")
    parser.add_argument('-c', '--hint-choices', 
        help="Number of hints considered (default: 5)", 
        action="store", default=5, dest="hc")
    args = parser.parse_args()

    HINTCHOICES = int(args.hc)
    main(args.storytree, args.hintfile, args.hintmodel,
        args.plotmodel, args.say, args.names,
        args.listnames, args.log, args.auto, args.speech, args.kw)