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

from datetime import datetime
import json
import os
import io
import pytz

from flask.globals import current_app
import requests
from flask import g, jsonify
from sqlalchemy import or_, and_

from server import redis_client
from server.utils.redis_util import RedisKey
from server.utils.db import collect_sql_error, Insert, Edit, Delete
from server.utils.page_util import PageUtil
from server.utils.response_util import RET
from server.utils.math_util import calculate_rate
from server.utils.open_api_util import BaseOpenApiHandler
from server.model.organization import Organization
from server.model.milestone import Milestone, IssueSolvedRate, TestReport
from server.model.mirroring import Repo
from server.model.template import Template
from server.model.product import Product
from server.model.task import TaskMilestone
from server.model.issue import Issue
from server.schema.milestone import GiteeMilestoneBase, GiteeMilestoneEdit, MilestoneStateEventSchema, QueryMilestoneByTimeSchema
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from server.utils.permission_utils import PermissionManager, GetAllByPermission
from server.utils.resource_utils import ResourceManager
from server.utils.md_util import MdUtil
from server.apps.issue.handler import GiteeV8BaseIssueHandler


class CreateMilestone:
    @staticmethod
    def bind_scope(milestone_id, body, api_info_file):
        cur_file_dir = os.path.abspath(__file__)
        cur_dir = cur_file_dir.replace(cur_file_dir.split("/")[-1], "")
        allow_list, deny_list = PermissionManager().get_api_list(
            "milestone", cur_dir + api_info_file, milestone_id
        )
        PermissionManager().generate(allow_list, deny_list, body)

    @staticmethod
    def run(body):
        if body.get("is_sync"):
            resp = MilestoneOpenApiHandler(body).create()
            if resp.get_json().get("error_code") != RET.OK:
                return resp
            milestone = Milestone.query.filter_by(
                name=body.get("name")).first()
            CreateMilestone.bind_scope(milestone.id, body, "api_infos.yaml")
            return jsonify(
                error_code=RET.OK, error_msg="Request processed successfully."
            )
        else:
            if body.get("start_time"):
                body["start_time"] = datetime.strptime(
                    body["start_time"], "%Y-%m-%d %H:%M:%S"
                )
            if body.get("end_time"):
                body["end_time"] = datetime.strptime(
                    body["end_time"], "%Y-%m-%d %H:%M:%S"
                )
            try:
                milestone_id = Insert(Milestone, body).insert_id(
                    Milestone, "/milestone"
                )
            except (IntegrityError, SQLAlchemyError) as e:
                raise RuntimeError(str(e)) from e
            CreateMilestone.bind_scope(milestone_id, body, "api_infos.yaml")
            return jsonify(
                error_code=RET.OK, error_msg="Request processed successfully."
            )


class DeleteMilestone:
    @staticmethod
    def single(milestone_id):
        milestone = Milestone.query.filter_by(id=milestone_id).first()
        if not milestone:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="milestone {} does not exist".format(milestone_id),
            )

        if milestone.is_sync is True:
            return MilestoneOpenApiHandler().delete(milestone_id)
        else:
            _tm = TaskMilestone.query.filter_by(
                milestone_id=milestone_id).all()
            if _tm:
                return jsonify(
                    error_code=RET.DATA_EXIST_ERR,
                    error_msg="Delete failed, Some tasks have been associated with this milestone"
                )
            return ResourceManager("milestone", "v2").del_cascade_single(
                milestone_id, Template, [
                    Template.milestone_id == milestone_id], False
            )


class MilestoneHandler:
    @staticmethod
    @collect_sql_error
    def get_milestone(query, filter_params = None):
        if not filter_params:
            filter_params = list()

        if query.name:
            filter_params.append(Milestone.name.like(f"%{query.name}%"))
        if query.type:
            filter_params.append(Milestone.type == query.type)
        if query.state:
            filter_params.append(Milestone.state == query.state)
        if query.is_sync:
            filter_params.append(Milestone.is_sync == query.is_sync)
        if query.round_id:
            filter_params.append(Milestone.round_id == query.round_id)
        if query.product_id:
            filter_params.append(Milestone.product_id == query.product_id)

        query_filter = Milestone.query.filter(*filter_params).order_by(
            Milestone.product_id, Milestone.name, Milestone.create_time
        )
        if query.create_time_order:
            if query.create_time_order == "ascend":
                query_filter = Milestone.query.filter(*filter_params).order_by(
                    Milestone.create_time.asc()
                )
            if query.create_time_order == "descend":
                query_filter = Milestone.query.filter(*filter_params).order_by(
                    Milestone.create_time.desc()
                )

        if not query.paged:
            milestones = query_filter.all()
            data = dict()
            items = []
            for _m in milestones:
                items.append(_m.to_json())
            data.update(
                {
                    "total": query_filter.count(),
                    "items": items,
                }
            )
            return jsonify(error_code=RET.OK, error_msg="OK", data=data)

        def page_func(item):
            milestone_dict = item.to_json()
            return milestone_dict

        page_dict, e = PageUtil.get_page_dict(
            query_filter, query.page_num, query.page_size, func=page_func
        )
        if e:
            return jsonify(
                error_code=RET.SERVER_ERR, error_msg=f"get milestone page error {e}"
            )

        return jsonify(error_code=RET.OK, error_msg="OK", data=page_dict)

    @staticmethod
    @collect_sql_error
    def get_all_gantt_milestones(query: QueryMilestoneByTimeSchema):
        """获取里程碑列表"""
        from server.model.group import Group, ReUserGroup
        current_org_id = redis_client.hget(
            RedisKey.user(g.gitee_id), 
            "current_org_id"
        )
        filter_params = [
            Milestone.permission_type == "org",
            Milestone.org_id == int(current_org_id),
            or_(
                Milestone.start_time.between(query.milestone_time[0], query.milestone_time[1]),
                Milestone.end_time.between(query.milestone_time[0], query.milestone_time[1])
            )
        ]

        re_user_groups = ReUserGroup.query.join(Group).filter(
            ReUserGroup.is_delete.is_(False),
            ReUserGroup.user_add_group_flag.is_(True),
            Group.is_delete.is_(False),
            ReUserGroup.org_id == int(current_org_id),
            ReUserGroup.user_gitee_id == g.gitee_id
        ).all()
        if re_user_groups:
            group_ids = [
                re_user_group.group_id for re_user_group in re_user_groups
            ]
            filter_params = [
                or_(
                    and_(
                        Milestone.permission_type == "org",
                        Milestone.org_id == int(current_org_id),
                    ),
                    and_(
                        Milestone.permission_type == "group",
                        Milestone.org_id == int(current_org_id),
                        Milestone.group_id.in_(group_ids),
                    ),
                ),
                or_(
                    Milestone.start_time.between(query.milestone_time[0], query.milestone_time[1]),
                    Milestone.end_time.between(query.milestone_time[0], query.milestone_time[1])
                )
            ]

        milestones = Milestone.query.filter(
            *filter_params
        ).all()
        return_data = [ milestone.to_gantt_dict() for milestone in milestones ]

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
            data=return_data,
        )


class MilestoneOpenApiHandler(BaseOpenApiHandler):
    def __init__(self, body=None):
        if body is not None:
            self.type = body.get("type")
            self.product_id = body.get("product_id")
            self.body = self.radia_2_gitee(body)
        super().__init__(Milestone, "/milestone")

    def gitee_2_radia(self, body):
        _body = self.body
        if isinstance(body.get("start_date"), str):
            _body["start_time"] = body.get("start_date")

        if isinstance(body.get("due_date"), str):
            _body["end_time"] = body.get("due_date")

        _body.update(
            {
                "gitee_milestone_id": body.get("id"),
                "name": body.get("title"),
                "type": self.type,
                "product_id": self.product_id,
                "is_sync": True,
            }
        )

        return _body

    def radia_2_gitee(self, body):
        if isinstance(body.get("start_time"), str):
            body["start_time"] = body.get("start_time")

        if isinstance(body.get("end_time"), str):
            body["end_time"] = body.get("end_time")

        return body

    @collect_sql_error
    def create(self):
        _url = "https://api.gitee.com/enterprises/{}/milestones".format(
            self.current_org.enterprise_id
        )

        return self.add_update(
            act="POST",
            url=_url,
            data=self.body,
            schema=GiteeMilestoneBase,
            handler=Insert,
        )

    def edit(self, milestone_id):
        _url = "https://api.gitee.com/enterprises/{}/milestones/{}".format(
            self.current_org.enterprise_id,
            milestone_id,
        )
        return self.add_update(
            act="PUT",
            url=_url,
            data=self.body,
            schema=GiteeMilestoneEdit,
            handler=Edit,
        )

    def delete(self, milestone_id):
        milestone = Milestone.query.filter_by(id=milestone_id).first()
        if not milestone:
            return jsonify(
                error_code=RET.NO_DATA_ERR, error_msg="the milestone not exist"
            )
        _tm = TaskMilestone.query.filter_by(milestone_id=milestone_id).all()
        if _tm:
            return jsonify(
                error_code=RET.DATA_EXIST_ERR,
                error_msg="Delete failed, Some tasks have been associated with this milestone"
            )

        _url = "https://api.gitee.com/enterprises/{}/milestones/{}".format(
            self.current_org.enterprise_id,
            milestone.gitee_milestone_id,
        )
        _resp = self.query(_url).get_json()
        if _resp.get("error_code") == RET.OK:
            if json.loads(_resp.get("data")).get("title") == milestone.name:
                return jsonify(
                    error_code=RET.RUNTIME_ERROR,
                    error_msg="you should delete this milestone in e.gitee.com first",
                )

        return ResourceManager("milestone", "v2").del_cascade_single(
            milestone_id, Template, [
                Template.milestone_id == milestone_id], False
        )

    def edit_state_event(self, milestone_id):
        _url = "https://api.gitee.com/enterprises/{}/milestones/{}".format(
            self.current_org.enterprise_id,
            milestone_id,
        )
        return self.add_update(
            act="PUT",
            url=_url,
            data=self.body,
            schema=MilestoneStateEventSchema,
            handler=Edit,
        )

    def get_milestones(self, params):
        _url = "https://api.gitee.com/enterprises/{}/milestones".format(
            self.current_org.enterprise_id,
        )
        _resp = self.query(url=_url, params=params)
        json_resp = _resp.get_json()
        if json_resp.get("error_code") == RET.OK:
            return jsonify(error_code=RET.OK, error_msg="OK", data=json.loads(json_resp.get("data")))
        return _resp


class GenerateVersionTestReport(GiteeV8BaseIssueHandler):
    def __init__(self, gitee_id=None, org_id=None) -> None:
        super().__init__(gitee_id, org_id)
        self.bug_issue_type_id = self.get_bug_issue_type_id("缺陷")

    def get_issues(self, gitee_milestone_id, state_ids):
        param = {
            "milestone_id": gitee_milestone_id,
            "issue_state_ids": state_ids,
            "issue_type_id": self.bug_issue_type_id,
        }
        resp = self.get_all(param)
        resp = resp.get_json()
        _data = None
        if resp.get("error_code") == RET.OK:
            data = json.loads(resp.get("data")).get("data")
            serious_data, main_data, minor_data, not_main_data, no_assign_data = [], [], [], [], []
            uri = "https://gitee.com"
            for d in data:
                priority = int(d.get("priority"))
                tmp_issue = {
                    "id": d.get("id"),
                    "ident": d.get("ident"),
                    "title": d.get("title"),
                    "url": "{}/{}" + "/issues/{}?from=project-issue".format(
                        uri,
                        d.get('project').get('path_with_namespace'),
                        d.get('ident')
                    ),
                    "priority": d.get("priority_human"),
                    "state": d.get("issue_state").get("title")
                }
                if priority == 4:
                    serious_data.append(tmp_issue)
                elif priority == 3:
                    main_data.append(tmp_issue)
                elif priority == 2:
                    minor_data.append(tmp_issue)
                elif priority == 1:
                    not_main_data.append(tmp_issue)
                else:
                    no_assign_data.append(tmp_issue)
            issue_data = serious_data + main_data + \
                minor_data + not_main_data + no_assign_data
            issue_data_cnt = len(issue_data)
            _data = {
                "serious_issue_rate": calculate_rate(len(serious_data), issue_data_cnt),
                "serious_issue_cnt": len(serious_data),
                "serious_issue": serious_data,
                "main_issue_rate": calculate_rate(len(main_data), issue_data_cnt),
                "main_issue_cnt": len(main_data),
                "main_issue": main_data,
                "minor_issue_rate": calculate_rate(len(minor_data), issue_data_cnt),
                "minor_issue_cnt": len(minor_data),
                "minor_issue": minor_data,
                "not_main_issue_rate": calculate_rate(len(not_main_data), issue_data_cnt),
                "not_main_issue_cnt": len(not_main_data),
                "not_main_issue": not_main_data,
                "no_assign_issue_rate": calculate_rate(len(no_assign_data), issue_data_cnt),
                "no_assign_issue_cnt": len(no_assign_data),
                "no_assign_issue": no_assign_data,
                "issue_data": issue_data,
                "issue_data_cnt": issue_data_cnt,
            }
        return _data

    def generate_update_test_report(self, milestone_id, uri):
        milestone = Milestone.query.filter_by(id=milestone_id).first()
        state_ids = self.get_state_ids_inversion(
            set(["已完成", "已验收", "已取消", "已拒绝", "已修复"])
        )
        data = self.get_issues(milestone.gitee_milestone_id, state_ids)
        if data is None:
            return jsonify(
                error_code=RET.BAD_REQ_ERR,
                error_msg="fail to get data through gitee openAPI",
            )

        state_ids = self.get_state_ids_inversion(
            set(["已取消", "已拒绝"])
        )
        param = {
            "milestone_id": milestone.gitee_milestone_id,
            "issue_state_ids": state_ids,
            "issue_type_id": self.bug_issue_type_id,
        }
        all_issue_cnt = self.get_issues_cnt(param)
        if all_issue_cnt is None:
            return jsonify(
                error_code=RET.BAD_REQ_ERR,
                error_msg="fail to get data through gitee openAPI",
            )
        state_ids = self.get_state_ids(
            set(["已验收"])
        )
        param = {
            "milestone_id": milestone.gitee_milestone_id,
            "issue_state_ids": state_ids,
            "issue_type_id": self.bug_issue_type_id,
        }
        accepted_issue_cnt = self.get_issues_cnt(param)
        if accepted_issue_cnt is None:
            return jsonify(
                error_code=RET.BAD_REQ_ERR,
                error_msg="fail to get data through gitee openAPI",
            )

        issue_info = ""
        issue_info2 = ""
        for d in data.get("issue_data"):
            issue_info += "|{}|{}|{}||{}|".format(
                d.get('ident'),
                d.get('title'),
                d.get('priority'),
                d.get('state')
            ) + "\n"
            issue_info2 += "|[{}]({})|{}|{}||{}|".format(
                d.get('ident'),
                d.get('url'),
                d.get('title'),
                d.get('priority'),
                d.get('state')
            ) + "\n"
        issue_info = issue_info[:-1]
        issue_info2 = issue_info2[:-1]

        issue_rate_info = "|数目|{}|{}|{}|{}|{}|{}|".format(
                data.get('issue_data_cnt'),
                data.get('serious_issue_cnt'),
                data.get('main_issue_cnt'),
                data.get('minor_issue_cnt'),
                data.get('not_main_issue_cnt'),
                data.get('no_assign_issue_cnt') 
            ) + "\n"
        issue_rate_info += "|百分比||{}|{}|{}|{}|{}|".format(
                data.get('serious_issue_rate'),
                data.get('main_issue_rate'),
                data.get('minor_issue_rate'),
                data.get('not_main_issue_rate'),
                data.get('no_assign_issue_rate')
            )
        repo_info = ""
        repo_info_tmp = ""
        repo = Repo.query.filter_by(milestone_id=milestone_id).first()
        if repo:
            repo_info = repo.content
            for rp in repo_info.split("\n"):
                if "baseurl" in rp:
                    repo_info_tmp += rp.split("/")[4] + ":" + "/".join(
                        rp.split("=")[1].split("/")[:-2]) + "\n"
        product_info = f"|{milestone.name}|{milestone.start_time}|{milestone.end_time}|"

        all_testcase_cnt = 0
        failed_testcase_cnt = 0
        succeed_testcase_cnt = 0
        test_result = f"|{milestone.name}|{all_testcase_cnt}|\
            {succeed_testcase_cnt}/{failed_testcase_cnt}|{all_issue_cnt}|"
        accepted_result = "{}版本，共计执行 {} 个测试用例，<br>1）发现{}个问题，\
            <br>2）发现{}个问题，且已经验收通过。<br>".format(
                milestone.name,
                all_testcase_cnt,
                all_issue_cnt,
                accepted_issue_cnt
            )

        timestamp = datetime.now(tz=pytz.timezone(
            'Asia/Shanghai')).strftime('%Y%m%d%H%M%S')
        tmp_filename = "server/static/test_report_template.md"
        md_filename = f"{current_app.config.get('TEST_REPORT_PATH')}/test_report_{timestamp}.md"
        html_filename = f"{current_app.config.get('TEST_REPORT_PATH')}/test_report_{timestamp}.html"
        fmd = io.open(md_filename, "w", encoding="utf-8")
        lines = io.open(tmp_filename, "r", encoding="utf-8").readlines()
        for line in lines:
            fmd.write(
                line.replace("<product_name>", milestone.name)
                .replace("<product_info>", product_info)
                .replace("<accepted_result>", accepted_result)
                .replace("<repo_info>", repo_info_tmp)
                .replace("<issue_info>", issue_info)
                .replace("<issue_rate>", issue_rate_info)
                .replace("<issue_info2>", issue_info2)
                .replace("<test_result>", test_result)
            )
        fmd.close()
        md_text = open(md_filename, "r", encoding="utf-8").read()
        MdUtil.md2html(md_text, html_filename)
        _test_report = TestReport.query.filter_by(
            milestone_id=milestone_id
        ).first()
        if _test_report:
            _test_report.md_file = f"test_report_{timestamp}.md"
            _test_report.html_file = f"test_report_{timestamp}.html"
            _test_report.add_update()
        else:
            _test_report = Insert(
                TestReport,
                {
                    "md_file": f"test_report_{timestamp}.md",
                    "html_file": f"test_report_{timestamp}.html",
                    "milestone_id": milestone_id,
                }
            ).insert_obj()

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
            data=_test_report.to_json()
        )


class IssueStatisticsHandlerV8():
    @staticmethod
    def get_gitee_id(org_id):
        access_token_list = redis_client.keys("access_token*")
        gitee_id = None
        for _token in access_token_list:
            _org_id = redis_client.hget(_token, "org_id")
            if int(_org_id) == int(org_id):
                gitee_id = _token.split("_")[-1]
                break
        return gitee_id

    @staticmethod
    def get_rate_by_milestone(milestone_id):
        _milestones = Milestone.query.filter_by(
            is_sync=True, id=milestone_id).first()
        if not _milestones:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="milestone does not exist/has no right",
            )
        isr = IssueSolvedRate.query.filter_by(
            gitee_milestone_id=_milestones.gitee_milestone_id).first()
        data = dict()
        if isr:
            data = isr.to_json()
        return jsonify(error_code=RET.OK, error_msg="OK", data=data)

    @staticmethod
    def update_issue_rate():
        from celeryservice.lib.issuerate import UpdateIssueRate
        from celeryservice.tasks import logger
        UpdateIssueRate(logger).main()
        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
        )

    @staticmethod
    def update_milestone_issue_rate(milestone_id):
        from celeryservice.lib.issuerate import UpdateIssueRate

        milestone = Milestone.query.filter_by(
            id=milestone_id, is_sync=True).first()
        if not milestone:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="milestone does not exist/has no right",
            )
        issue_rate = IssueSolvedRate.query.filter_by(
            gitee_milestone_id=milestone.gitee_milestone_id).first()
        if not issue_rate:
            Insert(
                IssueSolvedRate,
                {"milestone_id": milestone.id,
                    "gitee_milestone_id": milestone.gitee_milestone_id}
            ).single(IssueSolvedRate, "/issue_solved_rate")

        UpdateIssueRate.update_milestone_issue_resolved_rate(
            g.gitee_id,
            {"product_id": milestone.product_id, "org_id": milestone.product.org_id},
            milestone.gitee_milestone_id,
        )
        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
        )
