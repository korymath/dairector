# dAIrector: Automatic Story Beat Generation through Knowledge Synthesis

dAIrector is an automated director which collaborates with humans storytellers.

The system is based on work by Markus Eger [Plotter: Operationalizing the Master Book of All Plots](https://pdfs.semanticscholar.org/0c13/49ba53a155ca90dc6efe8ca3fe620fb50f88.pdf) and Kory Mathewson [Improvised Theatre Alongside Artificial Intelligences](https://aaai.org/ocs/index.php/AIIDE/AIIDE17/paper/view/15825).

This code accompanies the paper: [dAIrector: Automatic Story Beat Generation through Knowledge Synthesis](https://arxiv.org/abs/1811.03423) presented at Joint Workshop on Intelligent Narrative Technologies and Intelligent Cinematography and Editing at AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment (AIIDE'18). Edmonton, Alberta, Canada.

# Configure

Cross-platform compatible, tested on Windows and Mac OSX High Sierra 10.13.2.

## Installation for OSX

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
# get the trained model files
wget https://storage.googleapis.com/api-project-941639660937.appspot.com/tvtropes1_v.zip
wget https://storage.googleapis.com/api-project-941639660937.appspot.com/tvtropesmodel_opt.zip
# unpack the big files
unzip tvtropes1_v.zip
unzip tvtropesmodel_opt.zip
```

# Run

```sh
# first ensure that your environment is activated
source env/bin/activate
python markovgenerator.py -t outputfile.json plottoconflicts.json
python storyteller.py outputfile.json tvtropes.json tvtropesmodel.bin plottomodel.bin

# The storyteller is interactive, it understands the following commands:
# next [<cue>]
# hint [<cue>]
# quit
# next uses the vector model from plottomodel.bin to find the next story beat based on the given cue, and hint uses the tvtropesmodel.bin to find an appropriate trope.
```

## Basic Usage
Two human improvisors are on stage and at several points during an improvised performance they can cue the system to provide the next plot point. Then they improvise the dialog for each plot clause.

1. A single Plotto plot chain is generated, from a given A and C we could find 3 paths through B clauses.
2. Actors on stage are given the "next" beat of the story when they trigger the system.
3. Actors can also trigger a relevant entry from TV Tropes.

## Training a new model
```sh
python topicvectors.py tvtropesmodel.bin tvtropes.json
```

## Documentation
Go to [https://korymath.github.io/dairector/](https://korymath.github.io/dairector/)

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