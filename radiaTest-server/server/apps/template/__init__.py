# Copyright (c) [2022] Huawei Technologies Co.,Ltd.ALL rights reserved.
# This program is licensed under Mulan PSL v2.
# You can use it according to the terms and conditions of the Mulan PSL v2.
#          http://license.coscl.org.cn/MulanPSL2
# THIS PROGRAM IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
####################################
# @Author  : 
# @email   : 
# @Date    : 
# @License : Mulan PSL v2


#####################################

from flask_restful import Api

from .routes import TemplateEvent
from .routes import TemplateItemEvent, TemplateCloneEvent


def init_api(api: Api):
    api.add_resource(TemplateEvent, "/api/v1/template", "/api/v1/ws/<string:workspace>/template")
    api.add_resource(TemplateItemEvent, "/api/v1/template/<int:template_id>")
    api.add_resource(TemplateCloneEvent, "/api/v1/template/clone")
