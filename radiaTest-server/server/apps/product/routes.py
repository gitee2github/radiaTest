from flask.json import jsonify
from flask import request
from flask_restful import Resource
from flask_pydantic import validate

from server.model import Product, Milestone, TestReport
from server.utils.auth_util import auth
from server.utils.db import Edit, Select
from server.utils.page_util import PageUtil

from server.schema.product import ProductBase, ProductUpdate, ProductQueryBase
from server.utils.permission_utils import GetAllByPermission
from server.utils.resource_utils import ResourceManager
from server import casbin_enforcer
from server.utils.response_util import RET, response_collect


class ProductEventItem(Resource):
    @auth.login_required
    @validate()
    @casbin_enforcer.enforcer
    @response_collect
    def delete(self, product_id):
        return ResourceManager("product").del_cascade_single(
            product_id, Milestone, [Milestone.product_id == product_id], False
        )

    @auth.login_required
    @validate()
    @casbin_enforcer.enforcer
    @response_collect
    def get(self, product_id):
        return Select(Product, {"id": product_id}).single()

    @auth.login_required
    @validate()
    @casbin_enforcer.enforcer
    @response_collect
    def put(self, product_id, body: ProductUpdate):
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="product does not exist.",
            )
        name = product.name
        version = product.version
        if body.name:
            name = body.name
        if body.version:
            version = body.version

        product = Product.query.filter_by(
            name=name, version=version
        ).first()
        if product and product.id != product_id:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="The version of product has existed.",
            )
        _data = body.__dict__
        _data["id"] = product_id
        return Edit(Product, _data).single(Product, '/product')


class ProductEvent(Resource):
    @auth.login_required
    @validate()
    @response_collect
    def post(self, body: ProductBase):
        return ResourceManager("product").add("api_infos.yaml", body.__dict__)

    @auth.login_required
    @validate()
    def get(self, query: ProductQueryBase):
        query_filter = GetAllByPermission(Product).fuzz(
            query.__dict__,
            [Product.name.asc(), Product.create_time.asc()],
            "query"
        )
        return PageUtil.get_data(query_filter, query)


class PreciseProductEvent(Resource):
    @auth.login_required
    @response_collect
    def get(self):
        body = dict()

        for key, value in request.args.to_dict().items():
            if value:
                body[key] = value

        return GetAllByPermission(Product).precise(body)


class UpdateProductIssueRate(Resource):
    @auth.login_required
    @validate()
    @response_collect
    def put(self, product_id):
        from celeryservice.lib.issuerate import UpdateIssueRate
        from server.apps.milestone.handler import IssueStatisticsHandlerV8
        
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="product does not exist.",
            )
     
        user_id = IssueStatisticsHandlerV8.get_user_id(product.org_id)
        if user_id:
            UpdateIssueRate.update_product_issue_resolved_rate(
                user_id,
                {"product_id": product_id, "org_id": product.org_id},
            )

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
        )


class ProductTestReportEvent(Resource):
    @auth.login_required()
    @response_collect
    def get(self, product_id):
        _product = Product.query.filter_by(id=product_id).first()
        if not _product:
            return jsonify(
                error_code=RET.NO_DATA_ERR,
                error_msg="product doesn't exist.",
            )

        _test_reports = TestReport.query.join(Milestone).filter(
            TestReport.milestone_id == Milestone.id,
            Milestone.product_id == product_id
        ).all()
        data = []
        if _test_reports:
            data = [tr.to_json() for tr in _test_reports]

        return jsonify(
            error_code=RET.OK,
            error_msg="OK",
            data=data
        )
