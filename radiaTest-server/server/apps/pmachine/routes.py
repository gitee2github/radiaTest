# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2022-04-12 14:05:57
import datetime

from flask import request, jsonify, current_app
from flask_restful import Resource
from flask_pydantic import validate

from server.model import Pmachine, IMirroring, Vmachine
from server.model.pmachine import MachineGroup
from server.utils.db import Insert, Delete, Edit, Select, collect_sql_error
from server.utils.auth_util import auth
from server.utils.response_util import response_collect, RET
from server.schema.base import DeleteBaseModel
from server.schema.pmachine import (
    MachineGroupQuerySchema,
    MachineGroupUpdateSchema,
    PmachineBaseSchema,
    PmachineCreateSchema,
    PmachineQuerySchema,
    PmachineUpdateSchema,
    PmachineInstallSchema,
    PmachinePowerSchema,
    MachineGroupCreateSchema,
    HeartbeatUpdateSchema
)
from .handlers import PmachineHandler, PmachineMessenger, ResourcePoolHandler
from server.utils.resource_utils import ResourceManager


class MachineGroupEvent(Resource):
    @auth.login_required
    @response_collect
    @validate()
    def post(self, body: MachineGroupCreateSchema):
        return ResourceManager("machine_group").add_v2("pmachine/api_infos.yaml", body.__dict__)

    @auth.login_required
    @response_collect
    @validate()
    def get(self, query: MachineGroupQuerySchema):
        return ResourcePoolHandler.get_all(query)


class MachineGroupItemEvent(Resource):
    @auth.login_required
    @response_collect
    @validate()
    def put(self, machine_group_id, body: MachineGroupUpdateSchema):
        return ResourcePoolHandler.update_group(
            machine_group_id,
            body
        )

    @auth.login_required
    @response_collect
    @validate()
    def delete(self, machine_group_id):
        return ResourcePoolHandler.delete_group(machine_group_id)

    @auth.login_required
    @response_collect
    @validate()
    def get(self, machine_group_id):
        return ResourcePoolHandler.get(machine_group_id)


class MachineGroupHeartbeatEvent(Resource):
    @collect_sql_error
    @validate()
    def put(self, body: HeartbeatUpdateSchema):
        from_ip = request.remote_addr

        if str(body.messenger_ip) != from_ip:
            return jsonify(
                error_code=RET.UNAUTHORIZE_ERR,
                error_msg="the api only serve for messenger service, make sure the request is from valid messenger service"
            )
        
        machine_group = MachineGroup.query.filter_by(ip=from_ip).first()
        if not machine_group:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="the machine group does not exist"
            )

        current_datetime = datetime.datetime.now()

        if body.messenger_alive:
            machine_group.messenger_last_heartbeat = current_datetime
        if body.pxe_alive:
            machine_group.pxe_last_heartbeat = current_datetime
        if body.dhcp_alive:
            machine_group.dhcp_last_heartbeat = current_datetime
        
        machine_group.add_update(MachineGroup, "/machine_group", True)

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
        )


class PmachineItemEvent(Resource):
    @auth.login_required
    @response_collect
    @validate()
    def delete(self, pmachine_id):
        return ResourceManager("pmachine").del_cascade_single(pmachine_id, Vmachine, [Vmachine.pmachine_id==pmachine_id], False)
    
    @auth.login_required
    @response_collect
    @validate()
    def get(self, pmachine_id):
        return Select(Pmachine, {"id":pmachine_id}).single()

    @auth.login_required
    @response_collect
    @validate()
    def put(self, pmachine_id, body: PmachineUpdateSchema):
        pmachine = Pmachine.query.filter_by(id=pmachine_id).first()
        if not pmachine:
            return jsonify(
                error_code = RET.NO_DATA_ERR,
                error_msg = "The pmachine does not exist. Please check."
            )
        if body.state:
            if pmachine.state == body.state:
                return jsonify(
                    error_code = RET.VERIFY_ERR,
                    error_msg = "Pmachine state has not been modified. Please check."
                )

            if pmachine.state == "occupied" and pmachine.description == current_app.config.get("CI_HOST"):
                vmachine = Vmachine.query.filter_by(pmachine_id=pmachine.id).first()
                if vmachine:
                    return jsonify(
                        error_code = RPmachinePowerSchemaY_ERR,
                        error_msg = "Pmachine has vmmachine, can't release."
                    )
        _body = body.__dict__
        _body.update({"id": pmachine_id})

        return Edit(Pmachine, _body).single(Pmachine, "/pmachine")


class PmachineEvent(Resource):
    @auth.login_required
    @response_collect
    @validate()
    def post(self, body: PmachineCreateSchema):
        return ResourceManager("pmachine").add("api_infos.yaml", body.__dict__)

    @auth.login_required
    @response_collect
    @validate()
    def delete(self, body: DeleteBaseModel):
        return ResourceManager("pmachine").del_batch(body.__dict__.get("id"))

    @auth.login_required
    @response_collect
    @validate()
    def get(self, query: PmachineQuerySchema):
        return PmachineHandler.get_all(query)


class Install(Resource):
    @auth.login_required
    @response_collect
    @validate()
    def put(self, body: PmachineInstallSchema):
        pmachine = Pmachine.query.filter_by(
            id=body.id
        ).first()
        if not pmachine:
            return jsonify(
                error_code=RET.NO_DATA_ERR, 
                error_msg="the machine does not exist"
            )

        machine_group = pmachine.machine_group

        imirroring = IMirroring.query.filter_by(
            milestone_id=body.milestone_id
        ).first()
        if not imirroring:
            return jsonify(
                error_code=RET.NO_DATA_ERR, 
                error_msg="the iso mirror of this milestone does not exist"
            )
        
        _body = body.__dict__
        _body.update(
            {
                "pmachine": pmachine.to_json(),
                "mirroring": imirroring.to_json()
            }
        )

        messenger = PmachineMessenger(_body)
        return messenger.send_request(machine_group, "/api/v1/pmachine/install")


class Power(Resource):
    @auth.login_required
    @response_collect
    @validate()
    def put(self, body: PmachinePowerSchema):
        pmachine = Pmachine.query.filter_by(
            id=body.id
        ).first()
        if not pmachine:
            return jsonify(
                error_code=RET.NO_DATA_ERR, 
                error_msg="the machine does not exist"
            )

        machine_group = pmachine.machine_group

        _body = body.__dict__
        _body.update(
            {
                "pmachine": pmachine.to_json()
            }
        )

        messenger = PmachineMessenger(_body)
        return messenger.send_request(machine_group, "/api/v1/pmachine/")
