"""Build and validate clean installations outside the checkout on CI platforms."""

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import venv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    output = arguments.output.resolve()
    if output.is_relative_to(source):
        parser.error("--output must be outside the checkout")
    output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)

    def run(*command: str | Path, cwd: Path) -> None:
        subprocess.run(
            [str(part) for part in command],
            cwd=cwd,
            env=environment,
            check=True,
        )

    artifacts = output / "artifacts"
    run(
        sys.executable,
        "-m",
        "build",
        "--outdir",
        artifacts,
        source,
        cwd=output,
    )
    wheels = list(artifacts.glob("*.whl"))
    sdists = list(artifacts.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(f"Expected one wheel and sdist, got {wheels!r}, {sdists!r}")
    wheel, sdist = wheels[0], sdists[0]
    run(
        sys.executable,
        "-I",
        source / "tests" / "distribution_contents.py",
        "--source",
        source,
        "--wheel",
        wheel,
        "--sdist",
        sdist,
        cwd=output,
    )
    with tempfile.TemporaryDirectory(prefix="afcs-ci-", dir=output) as name:
        workspace = Path(name)
        extracted = workspace / "source"
        with tarfile.open(sdist) as archive:
            archive.extractall(extracted, filter="data")
        roots = list(extracted.iterdir())
        if len(roots) != 1 or not roots[0].is_dir():
            raise RuntimeError("The sdist must have exactly one source root")
        extracted_source = roots[0]
        smoke = extracted_source / "tests" / "distribution_smoke.py"
        config = (
            extracted_source
            / "config"
            / "campaigns"
            / "classical_pso_recommended_v2.example.json"
        )
        for mode, artifact, extras in (
            ("core", str(wheel), ()),
            ("extras", str(sdist) + "[analysis,opfunu]", ("--extras",)),
        ):
            environment_root = workspace / mode
            venv.EnvBuilder(with_pip=True).create(environment_root)
            python = (
                environment_root
                / ("Scripts" if os.name == "nt" else "bin")
                / ("python.exe" if os.name == "nt" else "python")
            )
            run(python, "-m", "pip", "install", artifact, cwd=workspace)
            run(python, "-m", "pip", "check", cwd=workspace)
            for workers in ("1", "2"):
                run(
                    python,
                    "-I",
                    smoke,
                    "--config",
                    config,
                    "--workers",
                    workers,
                    *extras,
                    cwd=workspace,
                )
            if mode == "extras":
                run(
                    python,
                    "-I",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-q",
                    cwd=extracted_source,
                )


if __name__ == "__main__":
    main()
