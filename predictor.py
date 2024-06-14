# -*- coding: utf-8 -*-
# @Author  : twd
# @FileName: predictor.py
# @Software: PyCharm

import os
from ETFC.model import *

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import numpy as np
from pathlib import Path
import argparse
import torch


def ArgsGet():
    parse = argparse.ArgumentParser(description='ETFC')
    parse.add_argument('-file', type=str, default='./test_data.fasta', help='fasta file')
    parse.add_argument('-out_path', type=str, default='./ETFC/result', help='output path')
    args = parse.parse_args()
    return args


def get_data(file):
    # getting file and encoding
    seqs = []
    names = []
    seq_length = []
    with open(file) as f:
        for each in f:
            if each == '\n':
                continue
            elif each[0] == '>':
                names.append(each)
            else:
                seqs.append(each.rstrip())

    # encoding
    amino_acids = 'XACDEFGHIKLMNPQRSTVWY'
    max_len = 50
    data_e = []
    delSeq = 0
    for i in range(len(seqs)):
        sign = True
        if len(seqs[i]) > max_len or len(seqs[i]) < 5:
            print(f'本方法只能识别序列长度在5-50AA的多肽，该序列将不能识别：{seqs[i]}')
            del names[i-delSeq]
            delSeq += 1
            continue
        length = len(seqs[i])
        seq_length.append(length)
        elemt, st = [], seqs[i]
        for j in st:
            if j == ',' or j == '1' or j == '0':
                continue
            elif j not in amino_acids:
                sign = False
                print(f'本方法只能识别包含天然氨基酸的多肽，该序列不能识别{seqs[i]}')
                del names[i-delSeq]
                delSeq += 1
                break

            index = amino_acids.index(j)
            elemt.append(index)
        if length <= max_len and sign:
            elemt += [0] * (max_len - length)
            data_e.append(elemt)

    return np.array(data_e), names, np.array(seq_length)


def predict(test, seq_length, h5_model):
    dir = './ETFC/dataset/Model/teacher/tea_model.pth'
    print('predicting...')

    # 1.loading model
    model = ETFC(50, 192, 21, 0.6, 1, 8)
    model.load_state_dict(torch.load(dir))

    # 2.predict
    model.eval()
    score_label = model(test, seq_length)

    for i in range(len(score_label)):
        for j in range(len(score_label[i])):
            if score_label[i][j] < 0.5:
                score_label[i][j] = 0
            else:
                score_label[i][j] = 1

    return score_label


def pre_my(test_data, seq_length, output_path, names):
    # models
    h5_model = []
    model_num = 10
    for i in range(1, model_num + 1):
        h5_model.append('model{}.h5'.format(str(i)))

    # prediction
    result = predict(test_data, seq_length, h5_model)

    # label
    peptides = ['AAP', 'ABP', 'ACP', 'ACVP', 'ADP', 'AEP', 'AFP', 'AHIVP', 'AHP', 'AIP', 'AMRSAP', 'APP', 'ATP',
                'AVP',
                'BBP', 'BIP',
                'CPP', 'DPPIP',
                'QSP', 'SBP', 'THP']
    functions = []
    for e in result:
        temp = ''
        for i in range(len(e)):
            if e[i] == 1:
                temp = temp + peptides[i] + ','
            else:
                continue
        if temp == '':
            temp = 'none'
        if temp[-1] == ',':
            temp = temp.rstrip(',')
        functions.append(temp)

    output_file = os.path.join(output_path, 'result.txt')
    with open(output_file, 'w') as f:
        for i in range(len(names)):
            f.write(names[i])
            f.write('functions:' + functions[i] + '\n')


if __name__ == '__main__':
    args = ArgsGet()
    file = args.file  # fasta file
    output_path = args.out_path  # output path

    # building output path directory
    Path(output_path).mkdir(exist_ok=True)

    # reading file and encoding
    data, names, seq_length = get_data(file)
    data = torch.LongTensor(data)
    seq_length = torch.LongTensor(seq_length)

    # prediction
    pre_my(data, seq_length, output_path, names)
