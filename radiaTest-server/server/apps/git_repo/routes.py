# Copyright (c) [2022] Huawei Technologies Co.,Ltd.ALL rights reserved.
# This program is licensed under Mulan PSL v2.
# You can use it according to the terms and conditions of the Mulan PSL v2.
#          http://license.coscl.org.cn/MulanPSL2
# THIS PROGRAM IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
####################################
# @Author  : Ethan-Zhang
# @email   : ethanzhang55@outlook.com
# @Date    : 
# @License : Mulan PSL v2


#####################################

from flask import jsonify, g
from flask_restful import Resource
from flask_pydantic import validate

from server import casbin_enforcer, redis_client
from server.utils.response_util import RET, workspace_error_collect
from server.utils.auth_util import auth
from server.utils.db import Insert, Edit
from server.utils.response_util import response_collect
from server.model.celerytask import CeleryTask
from server.model.framework import GitRepo
from server.model.template import Template
from server.schema.framework import GitRepoBase, GitRepoQuery, GitRepoScopedQuery
from server.apps.git_repo.handlers import GitRepoHandler
from server.utils.resource_utils import ResourceManager
from server.utils.permission_utils import GetAllByPermission


class GitRepoScopedEvent(Resource):
    @auth.login_required()
    @response_collect
    @validate()
    def get(self, query: GitRepoScopedQuery):
        filter_params = [
            GitRepo.permission_type == query.type
        ]
        if query.type == "group":
            filter_params.append(GitRepo.group_id == query.group_id)
        elif query.type == "org":
            filter_params.append(GitRepo.org_id == query.org_id)

        return GitRepoHandler.get_git_repo(query, filter_params)


class GitRepoEvent(Resource):
    @auth.login_required()
    @response_collect
    @validate()
    def post(self, body: GitRepoBase):
        return ResourceManager("git_repo").add_v2("framework/api_infos.yaml", body.__dict__)

    @auth.login_required()
    @response_collect
    @workspace_error_collect
    @validate()
    def get(self, workspace: str, query: GitRepoQuery):
        filter_params = GetAllByPermission(GitRepo, workspace).get_filter()
        return GitRepoHandler.get_git_repo(query, filter_params)


class GitRepoItemEvent(Resource):
    @auth.login_required
    @response_collect
    @validate()
    @casbin_enforcer.enforcer
    def delete(self, git_repo_id):
        return ResourceManager("git_repo").del_cascade_single(
            git_repo_id, 
            Template,
            [Template.git_repo_id == git_repo_id], 
            False
        )

    @auth.login_required
    @response_collect
    @validate()
    @casbin_enforcer.enforcer
    def put(self, git_repo_id, body: GitRepoQuery):
        _body = {
            **body.__dict__,
            "id": git_repo_id,
        }

        return Edit(GitRepo, _body).single(GitRepo, "/git_repo")

    @auth.login_required
    @response_collect
    @casbin_enforcer.enforcer
    def get(self, git_repo_id):
        git_repo = GitRepo.query.filter_by(id=git_repo_id).first()
        if not git_repo:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="the git repo does not exist"
            )

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
            data=git_repo.to_json()
        )



class GitRepoItemSyncEvent(Resource):
    @auth.login_required
    @response_collect
    @validate()
    @casbin_enforcer.enforcer
    def get(self, git_repo_id):
        """
        trigger 'read git repo' celery worker
        Args:
            git_repo_id(int): ID of the repo to sync
        Returns:
            Response: error_code(int), error_msg(str)
        """
        repo = GitRepo.query.filter_by(id=git_repo_id).first()
        if not repo or not repo.sync_rule:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg=f"repo #{git_repo_id} does not exist or not allow to resolve"
            )
        
        if not repo.adaptive:
            return jsonify(
                error_code=RET.BAD_REQ_ERR,
                error_msg=f"{repo.framework.name} is not adapted, the testcase repo could not be resolved"
            )

        if redis_client.get(f"loading_repo#{repo.id}_{repo.git_url}@{repo.branch}"):
            return jsonify(
                error_code=RET.RUNTIME_ERROR,
                error_msg=f"locked: repo#{repo.id} from {repo.git_url}@{repo.branch} has been loading"
            )

        from celeryservice.tasks import load_scripts
        _task = load_scripts.delay(
            repo.id,
            repo.name,
            repo.git_url,
            repo.branch,
        )
        celerytask = {
            "tid": _task.task_id,
            "status": "PENDING",
            "object_type": "scripts_load",
            "description": f"from {repo.git_url} on branch {repo.branch}",
            "user_id": g.gitee_id,
        }

        _ = Insert(CeleryTask, celerytask).single(CeleryTask, "/celerytask")

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
        )