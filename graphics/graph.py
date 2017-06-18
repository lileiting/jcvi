#!/usr/bin/env python
# -*- coding: UTF-8 -*-


"""
Script to plot diagrams of assembly graph in polyploids.
"""

from collections import defaultdict
from graphviz import Digraph
from itertools import combinations
from random import choice, sample

from jcvi.utils.iter import pairwise
from jcvi.utils.webcolors import css3_names_to_hex


def make_sequence(seq, name="S"):
    """
    Make unique nodes for sequence graph.
    """
    return ["{}_{}_{}".format(name, i, x) for i, x in enumerate(seq)]


def sequence_to_graph(G, seq, color='black'):
    """
    Automatically construct graph given a sequence of characters.
    """
    with G.subgraph(name=color) as c:
        c.attr('node', color=color)
        c.attr('edge', color=color)
        for x in seq:
            c.node(x)
        for a, b in pairwise(seq):
            c.edge(a, b)


def zip_sequences(G, allseqs, color="lightgray"):
    """
    Fuse certain nodes together, if they contain same data except for the
    sequence name.
    """
    for s in zip(*allseqs):
        groups = defaultdict(list)
        for x in s:
            part = x.split('_', 1)[1]
            groups[part].append(x)
        for part, g in groups.items():
            with G.subgraph(name=part) as c:
                #c.attr(margin='50')
                for a, b in combinations(g, 2):
                    c.edge(a, b, color=color, constraint="false")


def main():
    SIZE = 30
    PLOIDY = 6
    MUTATIONS = 5

    indices = range(SIZE)
    # Build fake data
    seqA = list("0" * SIZE)
    allseqs = [seqA[:] for x in range(PLOIDY)]  # Hexaploid
    for s in allseqs:
        for i in [choice(indices) for x in range(MUTATIONS)]:
            s[i] = "1"

    allseqs = [make_sequence(s, name=name) for (s, name) in \
                zip(allseqs, [str(x) for x in range(PLOIDY)])]

    # Build graph structure
    G = Digraph("Assembly graph", filename="graph")
    G.attr(rankdir='LR', nodesep="0.1", fontname="Helvetica")
    G.attr('node', shape='point')
    G.attr('edge', dir='none', penwidth='4')

    colors = sample(css3_names_to_hex.keys(), PLOIDY)
    print colors
    for s, color in zip(allseqs, colors):
        sequence_to_graph(G, s, color=color)
    zip_sequences(G, allseqs)

    # Output graph
    G.view()


if __name__ == '__main__':
    main()