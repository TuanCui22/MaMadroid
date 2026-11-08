"""Markov transition matrices, vectorised.

The 1.x implementation built the matrix with a triple Python loop over every
call in every app, then normalised row by row. For a corpus of a few thousand
APKs against a 400-node state space that is tens of millions of interpreted
iterations, and it was the slowest stage of the pipeline by a wide margin.

This version builds the same matrix with ``numpy.add.at`` over index arrays: one
pass to encode labels, one scatter-add, one normalisation. Same result, and the
row-normalisation is now explicit about the zero-row case instead of leaving a
silent all-zero row.

The public API is unchanged: ``main(imported, allnodes, wf)`` returns the same
``(len(allnodes), len(allnodes))`` float matrix.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


def encode(labels: Sequence[str], index: dict[str, int]) -> np.ndarray:
    """Map labels to their index, dropping anything unknown.

    Dropping unknown labels is deliberate: the state space is fixed by the
    reference lists, and a label outside it is not a state. The 1.x loop did the
    same thing implicitly by only appending on a match.
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
    """Encode and build in one call. Same contract as the 1.x ``main``."""
    return matrix_creation(dummy_coding(imported, alln, wf), alln)


def flatten(matrix: np.ndarray) -> list[float]:
    """Row-major flatten, matching the CSV column order of the 1.x output."""
    return [float(value) for value in matrix.reshape(-1)]
