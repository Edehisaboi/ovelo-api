import heapq
from typing import Dict, List, Tuple, Optional

class TopKQueue:
    """
    Lazy max-heap with update semantics:
      - Keep best score per id
      - Heap stores (-score, id); stale entries are ignored when popped/peeked
    """
    def __init__(self, k: int = 5):
        self.k = k
        self._heap: List[Tuple[float, str]] = []
        self._best: Dict[str, float] = {}

    def push(self, id: str, score: float) -> None:
        prev = self._best.get(id)
        if prev is None or score > prev:
            self._best[id] = score
            heapq.heappush(self._heap, (-score, id))
            # trim only when heap grows too large (amortised cheap)
            if len(self._heap) > 4 * self.k:
                self._prune()

    def _prune(self) -> None:
        # drop stale entries and reduce to ~2k to keep it lean
        new_heap = []
        for neg, id in self._heap:
            score = -neg
            if self._best.get(id) == score:
                new_heap.append((neg, id))
        heapq.heapify(new_heap)
        self._heap = new_heap[:2 * self.k]

    def top(self) -> Optional[Tuple[str, float]]:
        # Return current best without removing
        while self._heap:
            neg, _id = self._heap[0]
            score = -neg
            if self._best.get(_id) == score:
                return _id, score
            heapq.heappop(self._heap)  # stale
        return None

    def top_n(self, n: int) -> List[Tuple[str, float]]:
        # Snapshot of best N (cheap, non-destructive)
        self._prune()
        items = sorted(self._best.items(), key=lambda kv: kv[1], reverse=True)
        return items[:n]
