import re
from typing import Literal

from pydantic import AnyUrl
from pydantic import BaseModel as _BaseModel
from pydantic import ConstrainedStr, Extra, root_validator


class BaseModel(_BaseModel):
    # NOTE: Do this for repeatable, minified representation
    def dict(self, *args, **kwargs) -> dict:
        if "exclude_default" not in kwargs:
            kwargs["exclude_defaults"] = True

        return super().dict(*args, **kwargs)

    def json(self, *args, **kwargs) -> str:
        if "separators" not in kwargs:
            kwargs["separators"] = (",", ":")

        if "sort_keys" not in kwargs:
            kwargs["sort_keys"] = True

        if "exclude_default" not in kwargs:
            kwargs["exclude_defaults"] = True

        return super().json(*args, **kwargs)


class Name(ConstrainedStr):
    regex = re.compile("^[-A-Za-z0-9_]*$")
    min_length = 1


class DepPath(ConstrainedStr):
    regex = re.compile(r"^[A-Za-z0-9\./]*\.[a-z]*$")
    min_length = 1


class RelPath(ConstrainedStr):
    regex = re.compile(r"^\./[A-Za-z0-9\./]*\.[a-z]*$")
    min_length = 1


class Address(ConstrainedStr):
    regex = re.compile("^0x[A-Fa-f0-9]{40}$")
    min_length = 42
    max_length = 42


class Checksum(BaseModel):
    algorithm: str
    hash: str

    class Config:
        schema_extra = {
            "examples": [
                {
                    "algorithm": "sha256",
                    "hash": "abcd1234",
                }
            ]
        }


class Link(BaseModel):
    uri: AnyUrl
    checksum: Checksum | None = None

    class Config:
        schema_extra = {
            "examples": [{"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}]
        }


class ContractType(BaseModel):
    compiler: Name
    sources: list[RelPath | DepPath] = []
    deployments: dict[int, list[Address]] = {}
    output: Link | None = None

    class Config:
        schema_extra = {
            "examples": [
                {
                    "compiler": "solc-0.8.17",
                    "sources": [
                        "./file.sol",
                        "depA/file.sol",
                    ],
                    "output": {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"},
                }
            ]
        }


class Source(BaseModel):
    link: Link

    class Config:
        extra = Extra.allow  # May define additional fields
        schema_extra = {
            "examples": [
                {
                    "link": [{"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}],
                }
            ]
        }


class Compiler(BaseModel):
    bin: Link
    settings: dict = {}

    class Config:
        schema_extra = {
            "examples": [{"bin": {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}}]
        }


class Manifest(BaseModel):
    manifest: Literal["cpack/v1"]
    name: str = ""
    metadata: dict = {}
    types: dict[Name, ContractType] = {}
    sources: dict[RelPath, Source] = {}
    compilers: dict[Name, Compiler] = {}
    dependencies: dict[Name, Link] = {}

    @root_validator()
    def validate_types(cls, data):
        if "types" in data:
            for ct in data["types"].values():
                assert ct.compiler in data["compilers"]

                for src in ct.sources:
                    if src.startswith("./"):
                        assert src in data["sources"]
                    else:
                        assert "/" in src
                        assert src.split("/")[0] in data["dependencies"]

        return data

    class Config:
        schema_extra = {
            "examples": [
                {
                    "types": {
                        "MyContractType": {
                            "compiler": "solc-0.8.17",
                            "sources": [
                                "./file.sol",
                                "depA/file.sol",
                            ],
                            "output": {
                                "uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"
                            },
                        }
                    },
                    "sources": {
                        "./file.sol": {
                            "link": {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}
                        },
                    },
                    "compilers": {
                        "solc-0.8.17": {
                            "bin": {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}
                        }
                    },
                    "dependencies": {
                        "depA": {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}
                    },
                }
            ]
        }
