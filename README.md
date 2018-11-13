[![CircleCI](https://circleci.com/gh/korymath/dairector/tree/master.svg?style=svg)](https://circleci.com/gh/korymath/dairector/tree/master)

# dAIrector (🤖 + 📖)

dAIrector is an automated director which collaborates with humans storytellers.

## Documentation
Go to [https://korymath.github.io/dairector/](https://korymath.github.io/dairector/)

## Set Up

```sh
# install homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
# install and upgrade portaudio, swig, git, python3
brew install --upgrade portaudio swig git python3
# set up the python3 virtual environment
virtualenv -p python3 env
# activate the virtual environment
source env/bin/activate
# install requirements
pip install -r requirements.txt
# in case of an error with pyaudio, may need to point to brew intall directly
# see https://stackoverflow.com/questions/33513522/when-installing-pyaudio-pip-cannot-find-portaudio-h-in-usr-local-include 
# for more information
# pip install --global-option='build_ext' --global-option='-I/Users/korymath/homebrew/Cellar/portaudio/19.6.0/include' --global-option='-L/Users/korymath/homebrew/Cellar/portaudio/19.6.0/lib' pyaudio
# get the trained model and example files
wget https://storage.googleapis.com/api-project-941639660937.appspot.com/dairector_pretrained_examples.zip
# unpack the files
unzip dairector_pretrained_examples.zip
```

# Run

```sh
# first ensure that your environment is activated
source env/bin/activate
# example 1a, generate a new subgraph from the entire plotto conflict graph
python markovgenerator.py -t outputfile.json plottoconflicts.json
# example 1b, interactive story telling using the plot subgraph and tv tropes hints
python -W ignore storyteller.py outputfile.json tvtropes.json tvtropesmodel.bin plottomodel.bin
```

## Interactive Beat Generation

The storyteller is interactive, it understands the following commands:
* next [*cue_text*]
* hint [*cue_text*]
* quit

`next` uses the vector model from `plottomodel.bin` to find the next story beat based on the given cue text.

`hint` uses the `tvtropesmodel.bin` to find an appropriate trope.

## Basic Usage
Improvisors on stage can cue the system to provide the next plot point or the next hint.
The improvisors provide the dialogue for each plot clause.

## Training a new model
```sh
python topicvectors.py tvtropesmodel.bin tvtropes.json
```

## Cite

```sh
@inproceedings{eger2018dairector,
  author = {{Eger}, M. and {Mathewson}, K.~W.},
  title = "{dAIrector: Automatic Story Beat Generation through Knowledge Synthesis}",
  booktitle = {AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment (AIIDE18), Joint Workshop on Intelligent Narrative Technologies and Intelligent Cinematography and Editing},
  publisher = {AAAI},
  year = 2018,
  address={Edmonton, Alberta, Canada},
  month = 10,
}
```

## License

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.