import sys
import random
import pickle
import json
import numpy
import gensim.utils
from gensim.models.doc2vec import TaggedDocument, Doc2Vec


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
    #print(t, vec)
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
    #print(t, vec)
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
    return trainset[sims],w 
    
def get_model(fname):
    f = open(fname, "rb")
    m = pickle.load(f)
    f.close()
    return m
   

def main(outf, docfs):
    docs = set()
    random.seed(4)
    
    for d in docfs:
        f = open(d, "r")
        stats = json.load(f)
        f.close()
        for s in stats["states"]:
            if stats["states"][s]:
                docs.add(stats["states"][s][0]["text"])
    print("have", len(docs))
    (model,trainset) = train(docs, outf)
    for d in docfs:
        f = open(d, "r")
        stats = json.load(f)
        f.close()
        for s in stats["states"]:
            if stats["states"][s]:
                vec = list(map(float, list(model.infer_vector(gensim.utils.simple_preprocess(stats["states"][s][0]["text"]), steps=1000))))
                stats["states"][s][0]["vec"] = vec
        f = open(d.replace(".json", "_v.json"), "w")
        json.dump(stats, f, indent=4)
        f.close()
    

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
    print(documents[:2])
    (size, min_count, negative, iter, alpha, min_alpha, window) = (410, 2, 4, 900, 0.03, 0.01, 4) #(500, 2, 5, 150, 0.08, 0.02, 2)
    model = Doc2Vec(size=size, dm=0, window=window, min_count=min_count, negative=negative, epochs=iter, alpha=alpha, min_alpha=min_alpha, workers=3)
    model.build_vocab(documents)
    model.train(documents, total_examples=model.corpus_count, epochs=model.iter)
    f = open(outf, "wb")
    pickle.dump((model,trainset), f)
    f.close()
    correct = 0
    incorrect = 0
    for i,t in enumerate(trainset):
        (sims,w) = recall((model,trainset), t)
        if sims == t:
            correct += 1
        else:
            incorrect += 1
        #print(sims, t)
    print("performance:", correct*1.0/(correct + incorrect))
    ranks = []
    for t in testset:
        (sims,w) = recall((model,trainset), t)
        
        print(t, "\n   closest is:\n", sims, "\n  dist:", w, "\n\n")
    return (model,trainset)  
        
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])