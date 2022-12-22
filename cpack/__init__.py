from pydantic import BaseModel, ConstrainedStr
from pydantic import AnyUrl, FileUrl, Extra, root_validator, constr
from typing import Literal
import re


class Name(ConstrainedStr):
    regex = re.compile("^[-A-Za-z0-9_]*$")


class DepPath(ConstrainedStr):
    regex = re.compile("^[A-Za-z0-9\./]*\.[a-z]*$")


class RelPath(ConstrainedStr):
    regex = re.compile("^\./[A-Za-z0-9\./]*\.[a-z]*$")


class Address(ConstrainedStr):
    regex = re.compile("^0x[A-Fa-f0-9]{40}$")


class Checksum(BaseModel):
    algorithm: str = "sha256"
    hash: str = ""

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
            "examples": [
                {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}
            ]
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
                    "output": {
                        "uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"
                    },
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
                    "link": [
                        {"uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"}
                    ],
                }
            ]
        }


class Compiler(BaseModel):
    bin: Link
    settings: dict = {}

    class Config:
        schema_extra = {
            "examples": [
                {
                    "bin": {
                        "uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"
                    }
                }
            ]
        }


class Manifest(BaseModel):
    manifest: Literal["dpm/v1"]
    name: str = ""
    metadata: dict = {}
    types: dict[Name, ContractType] = {}
    sources: dict[RelPath, Source] = {}
    compilers: dict[Name, Compiler] = {}
    dependencies: dict[Name, Link] = {}

    @root_validator()
    def validate_types(cls, data):
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
        extra = Extra.allow  # May define additional fields
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
                            "link": {
                                "uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"
                            }
                        },
                    },
                    "compilers": {
                        "solc-0.8.17": {
                            "bin": {
                                "uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"
                            }
                        }
                    },
                    "dependencies": {
                        "depA": {
                            "uri": "ipfs://QmbBVxERnZ2ciQuRuZ45czd2DRgouCLEhibLWtC2CrH2j4"
                        }
                    },
                }
            ]
        }
