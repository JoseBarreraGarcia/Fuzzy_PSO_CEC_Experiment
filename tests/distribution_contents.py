"""Verify built archives against the intended source payload without extraction."""

import argparse
import hashlib
import json
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--sdist", type=Path, required=True)
    arguments = parser.parse_args()
    if not __debug__:
        parser.error("Run without -O: assertions enforce the artifact contract")
    source = arguments.source.resolve()
    runtime = {
        path.relative_to(source / "src").as_posix(): path
        for path in (source / "src" / "afcs").rglob("*")
        if path.is_file()
        and (
            path.suffix in {".py", ".sql", ".json", ".pkl"}
            or path.name == "LICENSE.txt"
        )
    }
    payload = {
        "README.md": source / "README.md",
        "pyproject.toml": source / "pyproject.toml",
        "MANIFEST.in": source / "MANIFEST.in",
    }
    for directory, suffixes in (
        ("src/afcs", {".py", ".md", ".json", ".sql", ".pkl", ".txt"}),
        ("tests", {".py", ".csv", ".md"}),
        ("config", {".json", ".md"}),
    ):
        for path in source.joinpath(*directory.split("/")).rglob("*"):
            if path.is_file() and path.suffix in suffixes:
                payload[path.relative_to(source).as_posix()] = path

    with (
        zipfile.ZipFile(arguments.wheel) as wheel,
        tarfile.open(arguments.sdist) as sdist,
    ):
        wheel_names = wheel.namelist()
        assert len(wheel_names) == len(set(wheel_names)), "Duplicate wheel members"
        assert {name for name in wheel_names if name.startswith("afcs/")} == set(
            runtime
        )
        metadata_names = [
            name for name in wheel_names if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_names) == 1, metadata_names
        metadata_directory = metadata_names[0].rsplit("/", 1)[0]
        assert all(
            name.startswith(("afcs/", metadata_directory + "/")) for name in wheel_names
        ), wheel_names
        package_metadata = BytesParser().parsebytes(wheel.read(metadata_names[0]))
        assert package_metadata["Name"] == "afcs"
        assert package_metadata["Requires-Python"] == ">=3.11"
        requirements = package_metadata.get_all("Requires-Dist")
        assert requirements == [
            "numpy>=2.0",
            'opfunu==1.0.1; extra == "opfunu"',
            'setuptools<82,>=68; extra == "opfunu"',
            'scipy>=1.11; extra == "analysis"',
            'matplotlib>=3.8; extra == "analysis"',
            'build==1.6.1; extra == "dev"',
            'ruff==0.17.4; extra == "dev"',
            'pyright==1.1.414; extra == "dev"',
        ], requirements
        assert b"afcs-campaign = afcs.experiments.cli:main" in wheel.read(
            metadata_directory + "/entry_points.txt"
        )
        members = sdist.getmembers()
        assert all(member.isfile() or member.isdir() for member in members)
        assert len({member.name for member in members}) == len(members)
        prefix = "afcs-" + package_metadata["Version"]
        assert all(
            member.name == prefix or member.name.startswith(prefix + "/")
            for member in members
        )
        files = {
            member.name[len(prefix) + 1 :]: member
            for member in members
            if member.isfile()
        }
        generated = {
            "PKG-INFO",
            "setup.cfg",
            *(
                "src/afcs.egg-info/" + name
                for name in (
                    "PKG-INFO",
                    "SOURCES.txt",
                    "dependency_links.txt",
                    "entry_points.txt",
                    "requires.txt",
                    "top_level.txt",
                )
            ),
        }
        assert set(files) == set(payload) | generated, (
            set(files) - set(payload) - generated,
            set(payload) - set(files),
        )
        for name, path in payload.items():
            stream = sdist.extractfile(files[name])
            assert stream is not None, name
            with stream:
                assert stream.read() == path.read_bytes(), name
        for name, path in runtime.items():
            assert wheel.read(name) == path.read_bytes(), name
        data_name = "afcs/problems/benchmarks/cec2017/data.pkl"
        assert hashlib.sha256(wheel.read(data_name)).hexdigest() == (
            "5f978ec6620e659ea933e21c4c4398b47b811467d3eed3dcb204566c3965924b"
        )

    print(
        json.dumps(
            {
                "runtime_files": len(runtime),
                "sdist_files": len(files),
                "wheel_entries": len(wheel_names),
                "artifacts": {
                    path.name: {
                        "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in (arguments.wheel, arguments.sdist)
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
