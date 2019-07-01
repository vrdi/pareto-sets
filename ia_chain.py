import csv
import os
from functools import partial
import json

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

from gerrychain import (
    Election,
    Graph,
    MarkovChain,
    Partition,
    accept,
    constraints,
    updaters,
)
from gerrychain.metrics import efficiency_gap, mean_median, polsby_popper
from gerrychain.proposals import recom
from gerrychain.updaters import cut_edges

newdir = "./IA_Outputs/"
os.makedirs(os.path.dirname(newdir + "init.txt"), exist_ok=True)
with open(newdir + "init.txt", "w") as f:
    f.write("Created Folder")
    
    unique_label = "GEOID10"
pop_col = "TOTPOP"
district_col = "CD"

graph_path = "./IA_counties/IA_counties.shp"

graph = Graph.from_file(graph_path, reproject = False)

graph.to_json("ia_json.json")

jgraph = Graph.from_json("ia_json.json")

df = gpd.read_file(graph_path)

def num_splits(partition):
    df["current"] = df[unique_label].map(dict(partition.assignment))
    splits = sum(df.groupby("CD")["current"].nunique() > 1)
    return splits
    
    def avg_pop_dist(partition):
    ideal_population = sum(partition["population"].values()) / len(
    partition
)
    total_deviation = sum([abs(v - ideal_population) for v in partition['population'].values()])
    return (total_deviation)/len(partition)

def pop_dist_pct(partition):
    ideal_population = ideal_population = sum(partition["population"].values()) / len(
    partition)
    total_deviation = total_deviation = sum([abs(v - ideal_population) for v in partition['population'].values()])
    avg_dist = total_deviation/len(partition)
    return avg_dist/ideal_population

my_updaters = {
    "cut_edges": cut_edges,
    "population": updaters.Tally("TOTPOP", alias = "population"),
    "avg_pop_dist": avg_pop_dist,
    "pop_dist_pct" : pop_dist_pct
}

num_elections = 3

election_names = [
    "PRES00",
    "PRES04",
    "PRES08",
]

election_columns = [
    ["PRES00D", "PRES00R"],
    ["PRES04D", "PRES04R"],
    ["PRES08D", "PRES08R"]
]

elections = [
    Election(
        election_names[i],
        {"Democratic": election_columns[i][0], "Republican": election_columns[i][1]},
    )
    for i in range(num_elections)
]

election_updaters = {election.name: election for election in elections}

my_updaters.update(election_updaters)

num_dist = 4

initial_partition = Partition(jgraph, "CD", my_updaters)

ideal_population = ideal_population = sum(initial_partition["population"].values()) / len(
    initial_partition
)

proposal = partial(
    recom, pop_col="TOTPOP", pop_target=ideal_population, epsilon=0.02, node_repeats=2
)

compactness_bound = constraints.UpperBound(
    lambda p: len(p["cut_edges"]), 2 * len(initial_partition["cut_edges"])
)

chain = MarkovChain(
    proposal=proposal,
    constraints=[
        constraints.within_percent_of_ideal_population(initial_partition, 0.02),
        compactness_bound,  # single_flip_contiguous#no_more_discontiguous
    ],
    accept=accept.always_accept,
    initial_state=initial_partition,
    total_steps=1000,
)

pop_vec = []
cut_vec = []
mms_vec = []
egs_vec = []
pop_dist_vec = []
pop_pct_vec = []
splits = []
votes = [[],[],[]]


t=0
for part in chain:
    splits.append(num_splits(part))

    pop_dist_vec.append(avg_pop_dist(part))
    pop_vec.append(sorted(list(part["population"].values())))
    cut_vec.append(len(part["cut_edges"]))
    mms_vec.append([])
    egs_vec.append([])
    pop_pct_vec.append(pop_dist_pct(part))
    
    for elect in range(num_elections):
        votes[elect].append(sorted(part[election_names[elect]].percents("Democratic")))
        mms_vec[-1].append(mean_median(part[election_names[elect]]))
        egs_vec[-1].append(efficiency_gap(part[election_names[elect]]))
        
    t += 1
    if t % 100 == 0:
        print(t)
        
plt.scatter(np.square(pop_pct_vec), cut_vec)
plt.title("Iowa 1000 %pop_dist vs #cut_edges")
plt.xlabel("square %pop distance from ideal")
plt.ylabel("#cut edges")
plt.savefig("cut_edges_pop_dist_1000")
