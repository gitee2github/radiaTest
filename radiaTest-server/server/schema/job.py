import datetime
from re import template
from typing import Optional

from pydantic import BaseModel, constr, root_validator

from server.schema import Frame
from server.schema.template import TemplateUpdate
from server.schema.base import UpdateBaseModel
from server.utils.db import Precise
from server.model import Milestone, Template


class RunSuiteBase(BaseModel):
    name: Optional[constr(max_length=64)]
    milestone_id: int
    frame: Frame
    testsuite: str

    @root_validator
    def assignment(cls, values):
        values["start_time"] = datetime.datetime.now()

        if not values.get("name"):
            milestone = Precise(
                Milestone, {"id": values.get("milestone_id")}).first()

            values["name"] = "Job-%s-%s-%s" % (
                milestone.name.replace(" ", "-"),
                values.get("frame"),
                datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            )
        return values


class RunTemplateBase(TemplateUpdate):
    frame: Frame
    taskmilestone_id: Optional[int]

    @root_validator
    def assignment(cls, values):
        values["start_time"] = datetime.datetime.now()

        template = Template.query.filter_by(id=values["id"]).first()

        values["template"] = template

        if not values.get("name"):
            values["name"] = "Job-%s-%s-%s" % (
                template.name.replace(" ", "-"),
                values.get("frame"),
                datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            )
        else:
            values["name"] = values["name"].replace(" ", "-")

        return values

class NewRunTemplateBase(BaseModel):
    template_id: int
    template_name: str
    name: Optional[str]
    frame: Frame
    taskmilestone_id: Optional[int]

    @root_validator
    def assignment(cls, values):
        values["start_time"] = datetime.datetime.now()

        if not values.get("name"):
            values["name"] = "Job-%s-%s-%s" % (
                values["template_name"].replace(" ", "-"),
                values.get("frame"),
                datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            )
        else:
            values["name"] = values["name"].replace(" ", "-")

        return values


class NewRunSuiteBase(RunSuiteBase):
    testsuite: Optional[str]
    suite_id: int


class AnalyzedUpdate(UpdateBaseModel):
    fail_type: Optional[str]
    details: Optional[str]
