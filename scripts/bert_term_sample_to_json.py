import argparse
import json
import numpy as np


def subword_weight_to_word_weight(subword_weight_str, m):
    fulltokens = []
    weights = []
    for item in subword_weight_str.split('\t'):
        token, weight = item.split(' ')
        weight = float(weight)
        token = token.strip()
        if token.startswith('##'):
            fulltokens[-1] += token[2:]
        else:
            fulltokens.append(token)
            weights.append(weight)
    assert len(fulltokens) == len(weights)
    fulltokens_filtered, weights_filtered = [], []
    selected_tokens = {}
    for token, w in zip(fulltokens, weights):
        if token == '[CLS]' or token == '[SEP]':
            continue
        if w * m < 1:
            continue
        tf = int(np.round(w * m))
        if tf < 1: continue
        selected_tokens[token] = max(tf, selected_tokens.get(token, 0))

    return selected_tokens
         
def tsv_to_weighted_doc(dataset_file_path,
                        prediction_file_path,
                        output_file_path,
                        m,
                        output_format):
    """

    :param dataset_file_path: tsv file
    :param prediction_file_path: json/tsv file of predictions
    :return: None
    """
    dataset = []
    predictions = []
    with open(dataset_file_path) as dataset_file, open(prediction_file_path) as prediction_file, open(output_file_path, 'w') as output_file:
        n, e, a = 0, 0, 0
        for l1, l2 in zip(dataset_file, prediction_file):
            n += 1
            if n % 10000 == 0: 
                print("processe {} lines, {} empty, avg len: {}".format(n, e, float(a)/(n - e)))
            did = line.split('\t')[0]
            selected_tokens = subword_weight_to_word_weight(l2, m)
            if not selected_tokens: 
                e += 1
                continue 
            sampled_tokens = []
            for t, tf in selected_tokens.items():
                sampled_tokens += [t] * tf
            dtext = ' '.join(sampled_tokens)
            if output_format == "tsv":
                output_file.write(did + '\t' + dtext.strip()  + '\n')
            elif output_format == "json":
                output_file.write(json.dumps({"id": did, "contents": dtext.strip()}))
                output_file.write("\n")
            a += len(sampled_tokens)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset_file', help='Dataset tsv file (collection.tsv.1)')
    parser.add_argument('prediction_file', help='DeepCT prediction file (test_result.tsv)')
    parser.add_argument('output_file', help='Output File')
    parser.add_argument('m', type=int, help='scaling parameter > 0, recommend 100')
    parser.add_argument('--output_format', type=str, choices=["tsv", "json"], default="tsv")
    args = parser.parse_args()

    assert args.m > 0

    tsv_to_weighted_doc(args.dataset_file,
                        args.prediction_file,
                        args.output_file, 
                        args.m,
                        args.output_format)

