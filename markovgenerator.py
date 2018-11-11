import sys
import pdb
import json
import random
import argparse


class Modifier(object):
    def apply(self, text):
        return text
    def apply_parts(self, xxx_todo_changeme):
        (start, end) = xxx_todo_changeme
        return start, end
    def apply_successor(self, succ):
        return succ

class ChangeModifier(Modifier):
    def __init__(self, original, replacement):
        self.original = original.strip('"')
        self.replacement = replacement.strip('"')
        self.active = True
    def apply(self, text):
        #print "changing", self.original, self.replacement
        tokens = text.split()
        result = []
        for t in tokens:
            if t.strip(",:'s") == self.original:
                result.append(t.replace(self.original, self.replacement))
            else:
                result.append(t)
        return " ".join(result)

class TransposeModifier(Modifier):
    def __init__(self, a, b):
        self.a = a.strip('"')
        self.b = b.strip('"')
        self.active = True
    def apply(self, text):
        #print "transposing", self.a, self.b
        tokens = text.split()
        result = []
        for t in tokens:
            if t.strip(",:'s") == self.a:
                result.append(t.replace(self.a, self.b))
            elif t.strip(",:'s") == self.b:
                result.append(t.replace(self.b, self.a))
            else:
                result.append(t)
        return " ".join(result)

class PartsModifier(Modifier):
    def __init__(self, fr, to):
        self.fr = fr
        self.to = to
        self.active = True
    def apply(self, text):
        self.active = False
        #print >> sys.stderr, self.fr, self.to
        #print >> sys.stderr, "orig", text
        if self.fr is not None and self.fr in text:
            start = text.find(self.fr)
            text = text[start:]
        if self.to is not None and self.to in text:
            end = text.find(self.to)
            text = text[:end]
        #print >> sys.stderr, "new", text
        return text

class NextStateModifier(Modifier):
    def __init__(self, next):
        self.next = next
        if not next:
            print('no next state to modify')
            raise ValueError
        self.active = True
    def apply_successor(self, next):
        self.active = False
        return self.next

class RemoveParens(Modifier):
    def __init__(self):
        self.active = True
    def apply(self, text):
        self.active = False
        tokens = text.split()
        result = []
        skip = 0
        for t in tokens:
            if t == "(":
                skip += 1
            elif t == ")":
                skip -= 1
            elif skip == 0:
                result.append(t)
        return " ".join(result)

class ModifierManager(object):
    def __init__(self, states):
        self.modifiers = []
        self.queue = []
        self.states = states

    def copy(self):
        result = ModifierManager(self.states)
        result.queue = self.queue[:]
        result.modifier = self.modifiers[:]
        return result

    def add(self, mod, doqueue=True, instate=""):
        #print "add", mod, self.queue, doqueue
        if self.queue and doqueue:
            item = self.queue[0].strip()
            self.queue = self.queue[1:]
            self.add(item, False, instate)
        if mod:
            futures = [s.strip() for s in mod.split(";")]
            if len(futures) > 1:
                if not self.queue:
                    next = futures[1]
                    tokens = next.split()
                    if tokens[0] in self.states:
                        self.modifiers.insert(0, NextStateModifier(tokens[0]))
                        if len(tokens) > 1:
                            futures[1] = " ".join(tokens[1:])
                        else:
                            del futures[1]
                    else:
                        if "," in next:
                            alts = next.split(",")
                            # e.g. 80a, b
                            if alts[0] in self.states:
                                poss = [alts[0]]
                                for a in alts[1:]:
                                    if alts[0][:-1] + a in self.states:
                                        poss.append(alts[0][:-1] + a)
                                self.modifiers.insert(0, NextStateModifier(random.choice(alts)))
                                del futures[1]
                    self.queue = futures[1:]
                mod = futures[0]
            cmd = ""
        if mod and mod != ", with the clause in parentheses":
            parts =  mod.split(",")
            while parts:
                part = parts[0]
                parts = parts[1:]
                skipping = False
                cmd = None
                if part.startswith("tr ") or part.startswith("ch "):
                    cmd = part[:2]
                    part = part[3:]
                prefix = part.split()[0]
                if "-" in prefix and not cmd:
                    #print >> sys.stderr, "part mod:", part
                    if prefix[0] == "-":
                        pm = PartsModifier(None, prefix[1:])
                        pm.source = (prefix, instate)
                        self.modifiers.insert(0, pm)
                    else:
                        fr, to = prefix.split("-")
                        pm = PartsModifier(fr, to)
                        pm.source = (prefix,instate)
                        self.modifiers.insert(0, pm)
                    skipping = True
                    if len(part.split()) > 1:
                        parts.insert(0, " ".join(part.split()[1:]))
                if cmd == "tr":
                    try:
                        tokens = part.split()
                        self.modifiers.append(TransposeModifier(tokens[0], tokens[2]))
                    except Exception:
                        return
                    if len(tokens) > 3:
                        tokens = tokens[3:]
                        if tokens[0] in ["&", ";"]:
                            tokens = tokens[1:]
                        parts.insert(0, " ".join(tokens))
                elif cmd == "ch":
                    modend = part.find(" to ")
                    if modend > 0:
                        orig = part[:modend]
                        repl = part[modend+4:]
                        if "&" in repl:
                            repls = repl.split("&", 1)
                            repl = repls[0]
                            nextrepl = repls[1].strip().split()[0].strip()
                            if nextrepl not in ["ch","tr"]:
                                repls[1] = "ch " + repls[1]
                            print("adding", repls[1:])
                            parts.insert(0, " ".join(repls[1:]))
                            print(parts)
                        self.modifiers.append(ChangeModifier(orig, repl))
                elif len(mod.strip()) == 1:
                    # stray a, b, c that doesn't exist
                    pass
                elif mod == "**********":
                    # whatever that's supposed to be
                    pass
                elif not skipping:
                    tokens = part.split()
                    if tokens[0] in self.states:
                        #print "next", tokens[0]
                        self.modifiers.insert(0, NextStateModifier(tokens[0]))
                        if len(tokens) > 1:
                            parts.insert(0, " ".join(tokens[1:]))
                    elif "add" in mod:
                        pass
                    elif "," in mod:
                        alts = mod.split(",")
                        # e.g. 80a, b
                        if alts[0] in self.states:
                            poss = [alts[0]]
                            for a in alts[1:]:
                                if alts[0][:-1] + a in self.states:
                                    poss.append(alts[0][:-1] + a)
                            self.modifiers.insert(0, NextStateModifier(random.choice(alts)))
                    elif mod == "without the clause in parentheses":
                        self.modifiers.insert(0, RemoveParens())
                    elif mod == 'change "married to" to "sweetheart of"':
                        self.modifiers.insert(0, ChangeModifier("married to", "sweetheart of"))
                    elif "or" in mod:
                        pass

    def modify(self, text):
        newmods = []
        for m in self.modifiers:
            text = m.apply(text)
            if m.active:
                newmods.append(m)
        self.modifiers = newmods
        result = list(filter(None, text.split("*")))
        if not result:
            return ""
        return random.choice(result)

    def modify_parts(self, parts):
        newmods = []
        for m in self.modifiers:
            parts = m.apply_parts(parts)
            if m.active:
                newmods.append(m)
        self.modifiers = newmods
        return parts

    def modify_successor(self, succ):
        newmods = []
        for m in self.modifiers:
            succ = m.apply_successor(succ)
            if m.active:
                newmods.append(m)
        self.modifiers = newmods
        return succ

def clean_tree(node):
    newchildren = []
    for n in node["children"]:
        if n:
            newchildren.append(n)
            clean_tree(n)
    node["children"] = newchildren

def generate(fname, stats="", state="", termination_probability=0.01,
    termination_length=0, debug=False, loops=False,
    user_input=True, treef=""):
    """Generation function."""

    deff = open(fname)
    termination_probability = float(termination_probability)
    if stats:
        user_input=False
    ostate = state
    chain = json.load(deff)
    deff.close()
    states = list(chain["states"].keys())
    global cnt, statecnt
    statecnt = len(states)
    if not state:
        state = random.choice(chain["initial_states"])
    modman = ModifierManager(states)
    visited = [state]
    currentlen = 1
    tree = {}
    treestates = [(state,[state],modman,tree)]
    while (termination_probability < 0.00001 or random.random() >= termination_probability) and (not termination_length or currentlen <= termination_length):
        currentlen += 1
        if state not in cnt:
            cnt[state] = 0
        cnt[state] += 1
        if not treef:
            text, eligible,p = next_step(chain, state, modman, visited, loops, stats, debug)
            if not eligible:
                break
            print(text)
            if not user_input:
                x = random.choice(eligible)
            else:
                x = None
                while x not in eligible:
                    print("\n  Possible next states:")
                    for e in eligible:
                        print("\t", e, modman.modify(chain["states"][e][0]["text"]))
                    print("\tchoice? ", end=' ')
                    x = input()
            next = modman.modify_successor(x)
            if next not in chain["states"]:
                next = random.choice(eligible)
            visited.append(next)
            found = False
            for s in p["successors"]:
                if s["successor"] == next:
                    try:
                        modman.add(s["modifier"], instate=state)
                    except Exception:
                        pass
                    found = True
        else:
            newtreestates = []
            for (s, vis, mm, node) in treestates:
                # if s == "998":
                    # print('s 998, error')
                try:
                    text, eligible, p = next_step(chain, s, mm, vis, loops, stats, debug)
                except (UnboundLocalError, KeyError) as error:
                    print('Error: {}'.format(error))
                if not eligible:
                    break
                node["text"] = text
                node["children"] = []
                for e in eligible:
                    e = mm.modify_successor(e)
                    newmm = mm.copy()
                    newnode = {}
                    node["children"].append(newnode)
                    for s in p["successors"]:
                        if s["successor"] == e:
                            try:
                                newmm.add(s["modifier"], instate=s)
                            except ValueError as error:
                                print('Error: {}'.format(error))
                                print(s)
                    newtreestates.append((e ,vis + [e],newmm,newnode))
            treestates = newtreestates
    if treef:
        print('treef: {}'.format(treef))
        if tree:
            clean_tree(tree)
        else:
            print('No tree to clean.')
            return False
        # write the tree to a file
        f = file(treef, "w")
        json.dump(tree, f, indent=True)
        f.close()
        return True

def next_step(chain, state, modman, visited, loops, stats, debug=False):
    parts = chain["states"][state]
    end = 1
    if len(parts) > 1:
        end = random.randint(1,len(parts))
    start,end = modman.modify_parts((0,end))
    for i,p in enumerate(parts[start:end]):
        if not stats:
            if debug:
                print(state, i, end=' ')
            text = modman.modify(p["text"])
        pass
    eligible = []
    for s in p["successors"]:
        if s["successor"] not in visited or loops:
            eligible.append(s["successor"])
    return text, eligible,p


file = open
cnt = {}
statecnt = 0


def main(fname, repeats=1, stats="", state="", termination_probability=0.01, termination_length=0, debug=False, loops=False, user_input=True, tree="", seed=1017):
    repeats = int(repeats)
    while repeats > 0:
        try:
            file_generated = generate(fname, stats, state, termination_probability, termination_length, debug, loops, user_input, tree)
        except (IndexError, ValueError) as error:
            random.seed(seed+random.randint(1, 1017))
            file_generated = generate(fname, stats, state, termination_probability, termination_length, debug, loops, user_input, tree)
        if not file_generated:
            random.seed(seed+random.randint(1, 1017))
            file_generated = generate(fname, stats, state, termination_probability, termination_length, debug, loops, user_input, tree)
        repeats -= 1
        if stats:
            print(".", end=' ')
        else:
            print("\n\n\n")
    if stats:
        s = 0
        cnts = []
        for c in cnt:
            cnts.append((c,cnt[c]))
            s += cnt[c]
        cnts.sort(key=lambda a_b: -a_b[1])
        print()
        for c in cnts[:10]:
            print(c)
        print("...")
        for c in cnts[-10:]:
            print(c)
        print("Average:", s*1.0/len(cnts))
        print("% Visited:", len(cnts)*1.0/statecnt, "(%d/%d)"%(len(cnts),statecnt))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a story from a Markov Chain description.')
    parser.add_argument('markovchain', help='The file describing the Markov Chain in JSON')
    parser.add_argument('--repeats', dest='repeats', type=int, default=1,
                       help='How many stories you want to generate (default: 1)')
    parser.add_argument('--stats', dest='stats', action="store_true", help="Print stats instead of stories", default=False)
    parser.add_argument('--start', '--state', dest='state', help="Force starting in this state (rather than random selection)", default="")
    parser.add_argument('--termination-probability', '--prob', dest='prob', type=float, help="Probability of not visiting next state, and terminating instead", default=0.01)
    parser.add_argument('--termination-length', '--len', dest="length", type=int, help="Maximum story length before generation terminates", default=0)
    parser.add_argument('--debug', '-d', dest="debug", action="store_true", help="Show fragment IDs")
    parser.add_argument('--loops', '-l', dest="loops", action="store_true", help="Allow loops")
    parser.add_argument('--auto-mode', '-a', dest="user", action="store_false", help="Don't ask for user input")
    parser.add_argument('--tree', '-t', dest='tree', action="store", help="Generate a branching story and save it in the given tree file", default="")
    parser.add_argument('--seed', dest='seed', action="store", help="random seed", type=int)

    args = parser.parse_args()

    # Set the random seed from the parsed arugment
    if args.seed:
        random.seed(args.seed)
    else:
        args.seed = random.randint(1, 1017)
        random.seed(args.seed)

    main(args.markovchain,
        repeats=args.repeats,
        stats=args.stats,
        state=args.state,
        termination_probability=args.prob,
        termination_length=args.length,
        debug=args.debug,
        loops=args.loops,
        user_input=args.user,
        tree=args.tree,
        seed=args.seed)
