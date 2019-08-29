from gerrychain import Partition

class ParetoCollection:
    """
    Calculates the Pareto front over a given set of scores for an arbitrary
    number of partitions.
    """
    def __init__(self, updaters):
        """
        :param updaters: The updaters to track.
        """
        self.updaters = updaters
        self.points = []

    def add(self, partitions):
        """Adds scores from one or more ``Partition``."""
        if isinstance(partitions, dict):
            if all(updater in partitions for updater in self.updaters):
                self.points.append(partitions)
        elif isinstance(partitions, Partition):
            self.points.append({updater: partitions[updater]
                                for updater in self.updaters})
        else:
            for partition in partitions:
                self.add(partition)

    def front(self, updaters=None, maxima=True):
        """
        Calculates the Pareto front over the collected set of scores.

        :param updaters: The subset of updaters to calculate the Pareto front
        over. If not specified, all tracked updaters are used.
        """
        # "Braindead" algorithm (to replace later)
        if not updaters:
            updaters = self.updaters
        if not self.points:
            return []
        optimal = [True] * len(self.points)
        traversed = [False] * len(self.points)
        queue = [0]
        while queue:
            idx = queue.pop()
            if traversed[idx]: continue
            traversed[idx] = True
            dominates, dominated_by = status(self.points, self.points[idx],
                                             updaters, optimal, maxima)
            for dom_idx in dominates:
                # If a point is dominated by at least one other point,
                # it cannot be optimal.
                optimal[dom_idx] = False
                traversed[dom_idx] = True
            to_queue = []
            if dominated_by:
                # If the point we're considering is dominated by
                # at least one other point, it can't be optimal.
                optimal[idx] = False
                for dom_idx in dominated_by:
                    if optimal[dom_idx] and not traversed[dom_idx]:
                        to_queue.append(dom_idx)
            if not to_queue:
                for point_idx, point_traversed in enumerate(traversed):
                    to_queue = []
                    if not point_traversed:
                        to_queue.append(point_idx)
                        break
            queue += to_queue
                
        return [self.points[idx] for idx, point_optimal
                in enumerate(optimal) if point_optimal]
    
    def __repr__(self):
        return (f'ParetoCollection ({len(self.points)} points, ' +
                f'{len(self.updaters)} dimensions)')
    
def status(points, compare_point, dimensions, optimal, maxima):
    point_dominates = []
    point_dominated_by = []
    for idx, point in enumerate(points):
        if optimal[idx]:
            if dominates(compare_point, point, dimensions):
                if maxima:
                    point_dominates.append(idx)
                else:
                    point_dominated_by.append(idx)
            elif dominates(point, compare_point, dimensions):
                if maxima:
                    point_dominated_by.append(idx)
                else:
                    point_dominates.append(idx)
    return point_dominates, point_dominated_by

def dominates(a, b, dimensions):
    """Determines if point a dominates point b."""
    geq = 0
    greater = False
    for dim in dimensions:
        if a[dim] > b[dim]:
            greater = True
        if a[dim] >= b[dim]:
            geq += 1
    return greater and geq == len(dimensions)