"""Markov transition matrices, vectorised.

A corpus of a few thousand APKs against a 400-node state space is tens of
millions of transitions. Building that with a nested Python loop per call is the
slowest possible shape for the work, so the matrix is assembled with
``numpy.add.at`` over index arrays: one pass to encode labels, one scatter-add,
one normalisation.

Row normalisation is explicit about the zero-row case: a state with no outgoing
transitions stays all-zero rather than becoming NaN, because "never left this
state" and "this state does not exist" are different facts.

Public API: ``main(imported, allnodes, wf)`` returns a
``(len(allnodes), len(allnodes))`` float matrix.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


def encode(labels: Sequence[str], index: dict[str, int]) -> np.ndarray:
    """Map labels to their index, dropping anything unknown.

    Dropping unknown labels is deliberate: the state space is fixed by the
    reference lists, and a label outside it is not a state.
    """
    return np.array([index[label] for label in labels if label in index],
                    dtype=np.int64)


def dummy_coding(imported: Iterable[str], allnodes: Sequence[str],
                 wf: str = "Y") -> list[np.ndarray]:
    """Encode each app's call sequence as indices into ``allnodes``.

    ``wf='Y'`` means the input is tab-separated (the abstracted-graph format);
    anything else means one label per line.
    """
    index = {node: position for position, node in enumerate(allnodes)}
    encoded: list[np.ndarray] = []
    for line in imported:
        labels = line.split("\t") if wf == "Y" else [line]
        labels = [label.strip() for label in labels if label.strip()]
        encoded.append(encode(labels, index))
    return encoded


def matrix_creation(encoded: Sequence[np.ndarray],
                    allnodes: Sequence[str]) -> np.ndarray:
    """Transition probabilities between states, row-normalised.

    A row with no outgoing transitions stays all-zero rather than becoming NaN:
    "this state was never left" and "this state does not exist" are different
    facts, and a NaN would poison every downstream feature.
    """
    size = len(allnodes)
    counts = np.zeros((size, size), dtype=np.float64)

    for sequence in encoded:
        if len(sequence) < 2:
            continue
        # Every call transitions from the first state of the app to that call.
        # That is what the original loop did: MarkovTransition[seq[0], seq[i]].
        np.add.at(counts, (sequence[0], sequence[1:]), 1.0)

    totals = counts.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        normalised = np.divide(counts, totals, out=np.zeros_like(counts),
                               where=totals != 0)
    return normalised


def main(imported: Iterable[str], alln: Sequence[str], wf: str = "Y") -> np.ndarray:
    """Encode and build in one call."""
    return matrix_creation(dummy_coding(imported, alln, wf), alln)


def flatten(matrix: np.ndarray) -> list[float]:
    """Row-major flatten, matching the CSV column order."""
    return [float(value) for value in matrix.reshape(-1)]
