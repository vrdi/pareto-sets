from random import random

def pareto_driver(partition, metrics, p=0.01):
    """
    If the proposed partition dominates the previous partition
    with respect to a set of scalar metrics, we accept the proposal
    with probability 1.
    
    Otherwise, we accept the proposal with probability ``p``.
    """
    dominant = True
    for metric in metrics:
        if partition[metric] >= partition.parent[metric]:
            dominant = False
            break
    return dominant or random() < p