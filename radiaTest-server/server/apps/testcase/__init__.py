from flask_restful import Api

from .routes import (
    BaselineEvent,
    BaselineItemEvent,
    BaselineImportEvent,
    SuiteEvent,
    CaseEvent,
    CaseImport,
    CaseRecycleBin
)


def init_api(api: Api):
    api.add_resource(BaselineEvent, "/api/v1/baseline")
    api.add_resource(
        BaselineItemEvent, 
        "/api/v1/baseline/<int:baseline_id>"
    )
    api.add_resource(
        BaselineImportEvent,
        "/api/v1/baseline/case_set",
    )
    api.add_resource(SuiteEvent, "/api/v1/suite")
    api.add_resource(CaseEvent, "/api/v1/case")
    api.add_resource(CaseImport, "/api/v1/case/import")
    api.add_resource(CaseRecycleBin, "/api/v1/case/recycle_bin")
