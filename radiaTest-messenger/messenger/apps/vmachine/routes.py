from flask import request
from flask_restful import Resource
from flask_pydantic import validate

from messenger.apps.vmachine.handlers import (
    CreateVmachine,
    DeleteVmachine,
    Control,
    DeviceManager,
    VmachineAsyncResultHandler,
)
from messenger.utils.response_util import runtime_error_collect
from messenger.schema.vmachine import (
    VdiskCreateSchema,
    VmachineBaseSchema,
    PowerSchema,
    VmachineItemSchema,
    VnicCreateSchema,
    DeviceDeleteSchema,
    DeviceBaseSchema,
)


class VmachineEventItem(Resource):
    @runtime_error_collect
    @validate()
    def delete(self, vmachine_id, body: VmachineItemSchema):
        _body = body.__dict__
        _body.update({"id":vmachine_id,})
        auth = request.headers.get("authorization")
        return DeleteVmachine(auth, _body).run()
    
    # TODO 更改内存、cpu
    # @runtime_error_collect
    # @validate()
    # def put(self, vmachine_id, body: VmachineUpdate):
            # _body = body.__dict__
            # _body.update({
            #     "id": vmachine_id
            #     "auth": request.headers.get("authorization")
            # })
    #     return EditVmachine(body.__dict__).work()


class VmachineEvent(Resource):
    @runtime_error_collect
    @validate()
    def post(self, body: VmachineBaseSchema):
        _body = body.__dict__
        auth = request.headers.get("authorization")
        return CreateVmachine(auth, _body).install()


class VmachineCallbackEvent(Resource):
    @runtime_error_collect
    def put(self):
        body = request.json
        auth = request.headers.get("authorization")

        return VmachineAsyncResultHandler.edit(auth, body)


class VmachineControl(Resource):
    @runtime_error_collect
    @validate()
    def put(self, vmachine_id, body: PowerSchema):
        _body = body.__dict__
        _body.update({
            "id": vmachine_id,
        })
        auth = request.headers.get("authorization")

        return Control(auth, _body).run()


class AttachDevice(Resource):
    @runtime_error_collect
    @validate()
    def post(self, body: DeviceBaseSchema):
        _body = body.__dict__
        auth = request.headers.get("authorization")

        return DeviceManager(
            auth,
            _body, 
            None, 
            "virtual/machine/attach"
        ).attach()


class VnicEvent(Resource):
    @runtime_error_collect
    @validate()
    def post(self, body: VnicCreateSchema):
        _body = body.__dict__
        auth = request.headers.get("authorization")

        return DeviceManager(
            auth,
            _body, 
            None, 
            "virtual/machine/vnic"
        ).add("vnic")

    @validate()
    def delete(self, body: DeviceDeleteSchema):
        _body = body.__dict__
        auth = request.headers.get("authorization")

        return DeviceManager(
            auth,
            _body, 
            None, 
            "virtual/machine/vnic"
        ).delete("vnic")


class VdiskEvent(Resource):
    @validate()
    def post(self, body: VdiskCreateSchema):
        _body = body.__dict__
        auth = request.headers.get("authorization")

        return DeviceManager(
            auth,
            _body, 
            None, 
            "virtual/machine/vdisk"
        ).add("vdisk")

    @validate()
    def delete(self, body: DeviceDeleteSchema):
        _body = body.__dict__
        auth = request.headers.get("authorization")

        return DeviceManager(
            auth,
            _body, 
            None, 
            "virtual/machine/vdisk"
        ).delete("vdisk")
