from typing import Optional, Literal
from pydantic import BaseModel, constr, root_validator

from server.model import Product
from server.utils.db import Precise
from server.schema.base import PermissionBase, TimeBaseSchema


class ProductBase(PermissionBase, TimeBaseSchema):
    name: constr(max_length=32)
    version: constr(max_length=32)
    description: Optional[constr(max_length=255)]
    version_type: Literal["LTS", "LTS-SPx", "INNOVATION"]
    is_forced_check: Optional[bool]

    @root_validator
    def check_duplicate(cls, values):
        product = Precise(
            Product, {"name": values.get("name"), "version": values.get("version")}
        ).first()
        if product:
            raise ValueError("The version of product has existed.")
        return values


class ProductUpdate(TimeBaseSchema):
    name: Optional[constr(max_length=32)]
    version: Optional[constr(max_length=32)]
    description: Optional[constr(max_length=255)]


class ProductQueryBase(BaseModel):
    name: Optional[constr(max_length=32)]
    version: Optional[constr(max_length=32)]
    description: Optional[constr(max_length=255)]


class ProductIssueRateFieldSchema(BaseModel):
    field: Literal["serious_resolved_rate", "main_resolved_rate",
                   "serious_main_resolved_rate", "current_resolved_rate", "left_issues_cnt"]