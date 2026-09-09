"""Deterministic dry-run for the era-research skill.

Safe by construction: candidates are integers, not executable generated code.
The objective is to discover x=7 by minimizing squared error.
"""

from era_engine import flat_ucb_search

TARGET = 7


def evaluate(x: int) -> float:
    return float((x - TARGET) ** 2)


def generate(parent: int, parent_score: float, iteration: int) -> int:
    # Deterministic set of research hypotheses/mutations.
    proposals = [1, 12, 4, 9, 6, 8, 7, 5]
    return proposals[iteration % len(proposals)]


def main() -> None:
    seed = 0
    seed_score = evaluate(seed)
    result = flat_ucb_search(
        initial_candidate=seed,
        initial_score=seed_score,
        generate_fn=generate,
        evaluate_fn=evaluate,
        iterations=8,
        direction="minimize",
        c_puct=1.0,
    )

    print("ERA-RESEARCH DRY RUN")
    print(f"baseline: candidate={seed}, score={seed_score:.1f}")
    for node in result.nodes:
        print(
            f"node={node.index:02d} parent={str(node.parent_index):>4} "
            f"candidate={node.candidate:>2} score={node.raw_score:>5.1f} "
            f"visits={node.visits:>2} status={node.status}"
        )
    print(f"best: candidate={result.best_candidate}, score={result.best_score:.1f}")
    if result.best_candidate != TARGET or result.best_score != 0.0:
        raise SystemExit("FAIL: dry-run did not recover the optimum")
    print("PASS: deterministic ERA-style loop recovered the known optimum")


if __name__ == "__main__":
    main()
