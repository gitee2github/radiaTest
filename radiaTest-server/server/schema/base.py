from typing import List
from enum import Enum
from pydantic import BaseModel, root_validator
from flask import g
from server import redis_client
from server.utils.redis_util import RedisKey
from . import PermissionType
from server.utils.db import Precise
from server.model import User, Group

class DeleteBaseModel(BaseModel):
    id: List[int]


class UpdateBaseModel(BaseModel):
    id: int


class PageBaseSchema(BaseModel):
    page_size: int = 10
    page_num: int = 1


class BaseEnum(Enum):
    @classmethod
    def code(cls, attr):
        if hasattr(cls, attr):
            return getattr(cls, attr).value
        else:
            return None

class PermissionBase(BaseModel):
    creater_id = int
    permission_type = PermissionType
    user_id = int
    group_id = int
    org_id = int

    @root_validator
    def check_exist(cls, values):
        user = Precise(
            User, {"gitee_id": values.get("creater_id"), "id": values.get("user_id")}
        ).first()
        if not user:
            raise ValueError("The user does not exist.")
        
        if values.get("creater_id") != g.gitee_id:
            raise ValueError("The user is not current login user.")
        
        if values.get("org_id") != redis_client.hget(RedisKey.user(g.gitee_id), "current_org_id"):
            raise ValueError("The org is not current login org.")

        if values.get("permission_type") == "group":
            if not values.get("group_id"):
                raise ValueError("Lack of group_id for a role of group")
            else:
                group = Precise(
                    Group, {"id": values.get("group_id"), "org_id": values.get("org_id")}
                ).first()
                if not group:
                    raise ValueError("The group does not exist or does not belong to current org.")
        return values
