import json
import re
from typing import List, Optional, Literal

from pydantic import BaseModel, HttpUrl, validator, root_validator

from server.schema import Operation, SortOrder


from server.schema.base import PageBaseSchema


class QualityBoardUpdateSchema(BaseModel):
    released: bool = False


class QualityBoardSchema(BaseModel):
    product_id: int


class CheckRound(BaseModel):
    rounds: str

    @validator("rounds")
    def check_rounds(cls, rounds):
        if rounds:
            pattern = re.compile(r"[0,1]*")
            if not pattern.findall(rounds):
                raise ValueError(
                    "rounds can only contain 1 and 0."
                )
            if rounds.count("1") != 1:
                raise ValueError(
                    "rounds must contain one digit 1."
                )
        return rounds


class CheckBaseline(BaseModel):
    baseline: str = None

    @validator("baseline")
    def check_ratio(cls, baseline):
        if baseline and '%' in baseline:
            _baseline = float(baseline.strip('%')) / 100.0
            if not 0 <= _baseline <= 1:
                raise ValueError("ratio baseline must be around 0-100%")
        else:
            try:
                _ = int(baseline)
            except ValueError as e:
                raise ValueError("baseline must be a ratio or a number") from e

        return baseline


class AddChecklistSchema(BaseModel):
    checkitem_id: int
    rounds: str = "0"
    baseline: str
    product_id: int
    operation: str

    @root_validator
    def check_values(cls, values):
        rounds = values.get("rounds")
        baseline = values.get("baseline")
        operation = values.get("operation")
        if rounds:
            pattern = re.compile(r"^[0,1]*1$")
            if len(rounds) == 1:
                pattern = re.compile(r"^[0,1]$")
            if not pattern.findall(rounds):
                raise ValueError(
                    "rounds can only contain 1 and 0, when length of round is bigger than 1, rounds must ends with 1."
                )
            _r_len = len(rounds)
            _bls = baseline.split(",")
            _bls_len = len(_bls)
            _ops = operation.split(",")
            _ops_len = len(_ops)
            if _r_len != _bls_len or _r_len != _ops_len:
                raise ValueError(
                    "rounds, baseline, operation must correspond to each other."
                )
            for bl in _bls:
                if '%' in bl:
                    _baseline = float(bl.strip('%')) / 100.0
                    if not 0 <= _baseline <= 1:
                        raise ValueError("ratio baseline must be around 0-100%")
                else:
                    try:
                        _ = int(baseline)
                    except ValueError as e:
                        raise ValueError("baseline must be a ratio or a number") from e
            for op in _ops:
                if op not in set(["<", ">", "=", "<=", ">="]):
                    raise ValueError("operation must be in ['<', '>', '=', '<=', '>=']")
        return values


class UpdateChecklistSchema(CheckRound, CheckBaseline):
    checkitem_id: int = None
    released: bool = None
    operation: Optional[Operation] = None


class DeselectChecklistSchema(CheckRound):
    rounds: str


class QueryChecklistSchema(PageBaseSchema):
    product_id: int = None


class ATOverviewSchema(PageBaseSchema):
    build_name: Optional[str]
    build_order: Optional[SortOrder] = "descend"


class CheckItemSchema(BaseModel):
    field_name : str
    title: str


class QueryCheckItemSchema(PageBaseSchema):
    field_name : Optional[str]
    title: Optional[str]


class FeatureListCreateSchema(BaseModel):
    no: str
    url: Optional[HttpUrl]
    feature: str
    sig: str
    owner: str
    release_to: str
    pkgs: str


class FeatureListQuerySchema(BaseModel):
    new: bool = True


class PackageListQuerySchema(BaseModel):
    summary: bool = False
    refresh: bool = False


class PackageCompareQuerySchema(PageBaseSchema):
    summary: bool = False
    search: Optional[str]
    arches: Optional[str]
    compare_result_list: Optional[str]
    desc: bool = False

    @validator("arches")
    def validate_arches(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        
        raise ValueError("the format of arches is not valid")

    @validator("compare_result_list")
    def validate_status(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        
        raise ValueError("the format of compare status list is not valid")


class QueryQualityResultSchema(BaseModel):
    type: Literal["issue", "AT"]
    product_id: int
    milestone_id: Optional[int]
    field: Literal["serious_resolved_rate", "main_resolved_rate",
                   "serious_main_resolved_rate", "current_resolved_rate", "left_issues_cnt"]
