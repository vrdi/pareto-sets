from random import random, choice
from collections import defaultdict
from gerrychain.tree import recursive_tree_part

def bvap_biased_recom(partition, pop_col, bvap_col, pop_target, epsilon,
                      node_repeats, target_districts, p_target):
    # TODO: Do we want to consider other denominators? (Voting-age population?)
    bvaps = defaultdict(int)
    pops = defaultdict(int)
    for node in partition.graph.nodes:
        bvaps[partition.assignment[node]] = partition.graph.nodes[node][bvap_col]
        pops[partition.assignment[node]] = partition.graph.nodes[node][pop_col]
    bvap_ratios = {
        district_idx: bvaps[district_idx] / district_pop
        for district_idx, district_pop in pops.items()
    }
    by_bvap = sorted(bvap_ratios.items(), key=lambda kv: kv[1])
    bvap_mapping = {
        bvap_idx: orig[0]
        for bvap_idx, orig in enumerate(by_bvap)
    }
    edges = sorted(partition['cut_edges'], key=lambda k: k[0])
    if random() < p_target:
        # With probability p_target, we uniformly choose a target
        # district to mix. Target indices are given by ordinal BVAP
        # (index 0 refers to the district with the loewst BVAP).
        target = choice(target_districts)
        # Get the district index of the district with the ordinal
        # BVAP value given by ``target``.
        district_idx = bvap_mapping[target]
        # print('Merging district', district_idx, '[', target, ']')
        district_edges = [edge for edge in edges
                          if partition.assignment[edge[0]] == district_idx]
        edge = choice(district_edges)
    else:
        # Otherwise, we just run a normal ReCom step.
        edge = choice(edges)
    parts_to_merge = (partition.assignment[edge[0]],
                      partition.assignment[edge[1]])

    # (copied from original ReCom proposal)
    subgraph = partition.graph.subgraph(
        partition.parts[parts_to_merge[0]] | partition.parts[parts_to_merge[1]]
    )

    try:
        flips = recursive_tree_part(
            subgraph,
            parts_to_merge,
            pop_col=pop_col,
            pop_target=pop_target,
            epsilon=epsilon,
            node_repeats=node_repeats,
        )
        return partition.flip(flips)
    except KeyError as ex:
        # TODO: Do something more robust here
        print('ReCom fails!')
        return partition
