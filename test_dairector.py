from markovgenerator import generate


def test_markov_generator(
    fname="plottoconflicts.json",
    repeats=1,
    stats=False,
    state="",
    termination_probability=0.01,
    termination_length=0,
    debug=False,
    loops=False,
    user_input=False,
    tree=""):
    """Test the generation."""
    story_generated = generate(fname, stats, state,
        termination_probability, termination_length, debug,
        loops, user_input, tree)
    assert story_generated == True