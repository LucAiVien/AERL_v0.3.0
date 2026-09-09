"""Safe empirical integration test for era-research.

Candidates are declarative, allow-listed scikit-learn pipeline specs. No generated
Python is executed. The frozen evaluator uses breast-cancer data bundled with
scikit-learn and macro-F1 on a fixed validation split.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from era_engine import flat_ucb_search


@dataclass(frozen=True)
class Candidate:
    family: str
    params: tuple[tuple[str, Any], ...] = ()

    def kwargs(self) -> dict[str, Any]:
        return dict(self.params)

    def label(self) -> str:
        p = ", ".join(f"{k}={v}" for k, v in self.params)
        return f"{self.family}({p})" if p else self.family


X, y = load_breast_cancer(return_X_y=True)
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.3, random_state=41, stratify=y
)


def evaluate(candidate: Candidate) -> float:
    kw = candidate.kwargs()
    if candidate.family == "logreg":
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=3000, random_state=0, **kw),
        )
    elif candidate.family == "svc":
        model = make_pipeline(StandardScaler(), SVC(**kw))
    elif candidate.family == "rf":
        model = RandomForestClassifier(random_state=0, n_jobs=1, **kw)
    elif candidate.family == "extra_trees":
        model = ExtraTreesClassifier(random_state=0, n_jobs=1, **kw)
    else:
        raise ValueError(f"unsupported family: {candidate.family}")
    model.fit(X_train, y_train)
    pred = model.predict(X_val)
    return float(f1_score(y_val, pred, average="macro"))


PROPOSALS = [
    Candidate("logreg", (("C", 0.25),)),
    Candidate("svc", (("C", 1.0), ("gamma", "scale"))),
    Candidate("rf", (("n_estimators", 150), ("max_depth", 6))),
    Candidate("extra_trees", (("n_estimators", 180), ("max_features", "sqrt"))),
    Candidate("svc", (("C", 2.0), ("gamma", "scale"))),
    Candidate("logreg", (("C", 1.0),)),
]


def generate(parent: Candidate, parent_score: float, iteration: int) -> Candidate:
    return PROPOSALS[iteration]


def main() -> None:
    seed = Candidate("logreg", (("C", 0.05),))
    seed_score = evaluate(seed)
    result = flat_ucb_search(
        initial_candidate=seed,
        initial_score=seed_score,
        generate_fn=generate,
        evaluate_fn=evaluate,
        iterations=len(PROPOSALS),
        direction="maximize",
        c_puct=1.0,
    )

    print("ERA-RESEARCH EMPIRICAL INTEGRATION TEST")
    print("Evaluation Contract: metric=macro-F1, direction=maximize, split=random_state=41")
    print(f"baseline: {seed.label()} score={seed_score:.6f}")
    for node in result.nodes:
        parent = "-" if node.parent_index is None else str(node.parent_index)
        print(
            f"node={node.index:02d} parent={parent:>2} "
            f"score={node.raw_score:.6f} visits={node.visits:02d} "
            f"candidate={node.candidate.label()}"
        )
    improvement = result.best_score - seed_score
    print(f"best: {result.best_candidate.label()} score={result.best_score:.6f}")
    print(f"absolute improvement: {improvement:+.6f}")

    # Clean rerun verification of the selected winner.
    rerun_score = evaluate(result.best_candidate)
    print(f"clean rerun: {rerun_score:.6f}")
    if abs(rerun_score - result.best_score) > 1e-12:
        raise SystemExit("FAIL: winner is not reproducible")
    if result.best_score < seed_score:
        raise SystemExit("FAIL: best candidate is worse than baseline")
    print("PASS: empirical loop completed and winner reproduced")


if __name__ == "__main__":
    main()
