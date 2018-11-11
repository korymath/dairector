import sys
import json
import numpy
import random
import pickle
import gensim.utils
from tqdm import tqdm
from gensim.models.doc2vec import TaggedDocument, Doc2Vec

import logging
logging.basicConfig(level=logging.INFO)
logging.info('Building topic model with gensim...')
random.seed(1017)


def cos_dist(v1,v2):
    return 1 - numpy.dot(gensim.matutils.unitvec(v1), gensim.matutils.unitvec(v2))

def preprocess(m, texts):
    (model,trainset) = m
    result = []
    for t in texts:
        result.append(model.infer_vector(gensim.utils.simple_preprocess(t), steps=1000))
    return result

def closestn_v(m, t, options, n=5):
    (model,trainset) = m
    vec = model.infer_vector(gensim.utils.simple_preprocess(t), steps=1000)
    result = None
    mindist = -1
    minat = None
    loptions = [(i,o) for (i,o) in enumerate(options)]
    def vdist(x):
        (i,v) = x
        return cos_dist(vec, v)
    loptions.sort(key=vdist)
    return loptions[:n]

def closest_v(m, t, options):
    (model,trainset) = m
    vec = model.infer_vector(gensim.utils.simple_preprocess(t), steps=1000)
    result = None
    mindist = -1
    minat = None
    for i,ovec in enumerate(options):
        d = cos_dist(vec, ovec)
        if mindist < 0 or d < mindist:
            result = ovec
            mindist = d
            minat = i
    return result,minat

def closest(m, t, options):
    (model,trainset) = m
    vec = model.infer_vector(gensim.utils.simple_preprocess(t))
    result = None
    mindist = -1
    minat = None
    for i,o in enumerate(options):
        ovec = model.infer_vector(gensim.utils.simple_preprocess(o))
        d = cos_dist(vec, ovec)
        if mindist < 0 or d < mindist:
            result = o
            mindist = d
            minat = i
    return result,minat

def recall(m, t):
    (model,trainset) = m
    vec = model.infer_vector(gensim.utils.simple_preprocess(t))
    (sims,w) = model.docvecs.most_similar([vec], topn=len(model.docvecs))[0]
    return trainset[sims], w

def get_model(fname):
    f = open(fname, "rb")
    m = pickle.load(f)
    f.close()
    return m

def train(docs, outf="model.bin"):
    docs = list(docs)
    random.shuffle(docs)
    testset = []
    trainset = []
    n = int(round(0.9*len(docs)))
    for d in docs:
        if len(trainset) < n and len(d.split()) > 2:
            trainset.append(d)
        else:
            testset.append(d)
    documents = []
    for i,d in enumerate(trainset):
        documents.append(TaggedDocument(gensim.utils.simple_preprocess(d), [i]))

    # Topic model variables
    size = 256
    min_count = 2
    negative = 4
    iterations = 10
    alpha = 0.03
    min_alpha = 0.01
    window = 4

    # Train the model with DOC2VEC
    model = Doc2Vec(
        vector_size=size,
        dm=0,
        window=window,
        min_count=min_count,
        negative=negative,
        epochs=iterations,
        alpha=alpha,
        min_alpha=min_alpha,
        workers=8)

    model.build_vocab(documents)
    model.train(documents,
        total_examples=model.corpus_count,
        epochs=model.iter)

    logging.info('Saving model.')
    f = open(outf, "wb")
    pickle.dump((model,trainset), f)
    f.close()
    logging.info('Model saved.')

    # Track the performance on the training set
    correct = 0
    incorrect = 0
    for i,t in enumerate(tqdm(trainset)):
        (sims, w) = recall((model, trainset), t)
        if sims == t:
            correct += 1
        else:
            incorrect += 1
    logging.info("Training accuracy: {}".format(correct*1.0/(correct + incorrect + 0.00001)))

    # Track the performance on the test set
    test_correct = 0
    test_incorrect = 0
    for i,t in enumerate(tqdm(testset)):
        (sims, w) = recall((model, trainset), t)
        if sims == t:
            test_correct += 1
        else:
            test_incorrect += 1
    logging.info("Test accuracy: {}".format(test_correct*1.0/(test_correct + test_incorrect + 0.00001)))
    # logging.info(t, "\n   closest is:\n", sims, "\n  dist:", w, "\n\n")
    return (model, trainset)


def main(outf, docfs):
    """ Main run code for training a topic model."""
    docs = set()
    for d in docfs:
        f = open(d, "r")
        stats = json.load(f)
        f.close()
        for s in stats["states"]:
            if stats["states"][s]:
                docs.add(stats["states"][s][0]["text"])
    # Train the model.
    (model, _) = train(docs, outf)

    # Use the newly trained model to make vectors of the docs
    # Save the vectors to a file
    for d in tqdm(docfs):
        f = open(d, "r")
        stats = json.load(f)
        f.close()
        for s in stats["states"]:
            if stats["states"][s]:
                vec = list(map(float, list(model.infer_vector(gensim.utils.simple_preprocess(stats["states"][s][0]["text"]), epochs=10))))
                stats["states"][s][0]["vec"] = vec
        f = open(d.replace(".json", "_v.json"), "w")
        json.dump(stats, f, indent=4)
        f.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])