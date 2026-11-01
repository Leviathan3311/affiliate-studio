"""Build Kaggle artifacts from the percent-format sources.

    KAGGLE_USERNAME=you python notebooks/kaggle/build.py

Creates notebooks/kaggle/dist/
  dataset/   gp_worker.py + workflows/*.json (flat) -> `kaggle datasets create -p dist/dataset`
  nb1/, nb2/ notebook + kernel-metadata  -> `kaggle kernels push -p dist/nb1`
"""

import json
import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
DIST = HERE / "dist"
USER = os.environ.get("KAGGLE_USERNAME", "your-kaggle-username")
DATASET = f"{USER}/growthpilot-worker"
KERNELS = {
    "nb1": ("nb1_generative_studio.py", "GrowthPilot Generative Studio"),
    "nb2": ("nb2_shorts_repurposer.py", "GrowthPilot Shorts Repurposer"),
}


def to_ipynb(src: str) -> dict:
    cells = []
    for chunk in re.split(r"^# %%", src, flags=re.M)[1:]:
        header, _, body = chunk.partition("\n")
        if header.strip() == "[markdown]":
            text = "\n".join(line.removeprefix("# ").removeprefix("#") for line in body.strip().splitlines())
            cells.append({"cell_type": "markdown", "metadata": {}, "source": text})
        else:
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                          "source": body.strip("\n")})
    return {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3",
                                                        "language": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


def main() -> None:
    shutil.rmtree(DIST, ignore_errors=True)
    ds = DIST / "dataset"
    ds.mkdir(parents=True)
    shutil.copy(HERE / "gp_worker.py", ds)
    for f in (HERE / "workflows").glob("*.json"):  # flat: `kaggle datasets` skips subfolders
        shutil.copy(f, ds)
    (ds / "dataset-metadata.json").write_text(json.dumps(
        {"title": "growthpilot-worker", "id": DATASET, "licenses": [{"name": "other"}]}, indent=2))
    for name, (src, title) in KERNELS.items():
        out = DIST / name
        out.mkdir()
        nb_file = f"{name}.ipynb"
        (out / nb_file).write_text(json.dumps(to_ipynb((HERE / src).read_text()), ensure_ascii=False, indent=1))
        (out / "kernel-metadata.json").write_text(json.dumps({
            "id": f"{USER}/{title.lower().replace(' ', '-')}",
            "title": title,
            "code_file": nb_file,
            "language": "python",
            "kernel_type": "notebook",
            "is_private": True,
            "enable_gpu": True,
            "machine_shape": "NvidiaTeslaT4",  # Kaggle "GPU T4 x2"
            "enable_internet": True,
            "dataset_sources": [DATASET],
            "competition_sources": [],
            "kernel_sources": [],
        }, indent=2))
    print("built", DIST)


if __name__ == "__main__":
    main()
