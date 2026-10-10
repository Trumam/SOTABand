"""Run the offline hypoxemia acceptance flow with synthetic, non-patient data.

Run with the dedicated PyTorch interpreter. Set SOTABAND_RUNTIME_ROOT to an
isolated directory before starting this script.
"""

from __future__ import annotations

import json
import os
import pickle
import runpy
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.runtime.paths import RUNTIME_ROOT
from core.task.task_manager import TaskManager
from core.timeseries.manifests import write_dataset_manifest


def main() -> None:
    if "SOTABAND_RUNTIME_ROOT" not in os.environ:
        raise RuntimeError("Set SOTABAND_RUNTIME_ROOT to an isolated directory")
    project = Path(__file__).resolve().parents[1]
    tool = runpy.run_path(str(project / "resources/tools/implementations/timeseries-classification-runner/tool.py"))
    dataset = RUNTIME_ROOT / "synthetic-windows"
    dataset.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    features = []
    info = []
    for group in range(24):
        for sample in range(2):
            positive = group % 2 == 0
            window = np.column_stack((
                np.arange(256),
                97 - (4 if positive else 0) + rng.normal(0, 0.2, 256),
                75 + rng.normal(0, 1, 256),
                75 + rng.normal(0, 1, 256),
                16 + rng.normal(0, 0.5, 256),
                2 + rng.normal(0, 0.1, 256),
            ))
            features.append(window)
            info.append({"features": ["Time", "SpO2", "HR", "PR", "RR", "PI"],
                         "sample_type": "hypoxemia" if positive else "normal",
                         "group_id": f"synthetic-{group:02d}", "sample": sample})
    with (dataset / "window_features.pkl").open("wb") as handle:
        pickle.dump(features, handle)
    with (dataset / "window_info.pkl").open("wb") as handle:
        pickle.dump(info, handle)
    stats = {"lookback_seconds": 256, "sampling_hz": 1, "interval_seconds": 30,
             "total_windows": 48, "hypoxemia_windows": 24, "non_hypoxemia_windows": 24}
    (dataset / "window_stats.json").write_text(json.dumps(stats), encoding="utf-8")
    write_dataset_manifest(dataset, dataset_id="synthetic-pr-acceptance",
                           feature_order=["SpO2", "HR", "PR", "RR", "PI"],
                           sequence_length=256, sampling_hz=1)

    validated = tool["execute"](mode="validate", source_path=str(dataset))
    assert validated["status"] == "success", validated
    requested = tool["execute"](
        mode="train", dataset=str(dataset), model_id="SegRNN",
        training_config={"epochs": 1, "batch_size": 8, "use_ema": False,
                         "early_stop_patience": 0},
        model_config={"d_model": 32},
    )
    assert requested["status"] == "success", requested
    task = TaskManager().submit(**requested["data"]["task_request"])
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        task = TaskManager().get(task["id"])
        if task["status"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(2)
    assert task["status"] == "completed", {
        "status": task["status"], "message": task.get("message"),
        "log_tail": task.get("log_tail", "")[-2000:],
    }
    artifact = Path(task["metadata"]["artifact_path"])
    saved = tool["execute"](mode="inspect-model", artifact_path=str(artifact),
                            dataset_id="synthetic-pr-acceptance", register_model=True)
    assert saved["status"] == "success", saved
    model_id = saved["data"]["model_id"]
    evaluated = tool["execute"](mode="evaluate", dataset=str(dataset),
                                model_id=model_id, export_excel=True)
    assert evaluated["status"] == "success", evaluated
    result = evaluated["data"]
    assert result["model_resource_id"] == model_id, result
    assert Path(result["model_artifact"]).resolve() == artifact.resolve(), result
    assert result["source_dataset_window_count"] == 48, result
    excel = Path(result["excel_path"])
    assert excel.is_file() and zipfile.is_zipfile(excel), excel

    mismatched = dataset / "dataset_manifest.json"
    original = mismatched.read_text(encoding="utf-8")
    try:
        manifest = json.loads(original)
        manifest["sampling_hz"] = 2
        mismatched.write_text(json.dumps(manifest), encoding="utf-8")
        rejected = tool["execute"](mode="evaluate", dataset=str(dataset), model_id=model_id)
        assert rejected["status"] != "success", rejected
    finally:
        mismatched.write_text(original, encoding="utf-8")

    feature_file = dataset / "window_features.pkl"
    original_windows = feature_file.read_bytes()
    try:
        shortened = pickle.loads(original_windows)
        shortened[0] = shortened[0][:-1]
        with feature_file.open("wb") as handle:
            pickle.dump(shortened, handle)
        rejected_length = tool["execute"](mode="evaluate", dataset=str(dataset), model_id=model_id)
        assert rejected_length["status"] != "success", rejected_length
    finally:
        feature_file.write_bytes(original_windows)

    print(json.dumps({
        "task_id": task["id"], "model_id": model_id,
        "artifact_path": str(artifact), "dataset_path": str(dataset),
        "evaluation_scope": result["evaluation_scope"],
        "evaluation_window_count": result["dataset_window_count"],
        "metrics": result["validation"], "excel_path": str(excel),
        "sampling_mismatch_rejected": True,
        "short_window_rejected": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
