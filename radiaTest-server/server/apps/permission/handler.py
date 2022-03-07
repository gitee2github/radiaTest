from flask import jsonify

from server import db
from server.model.organization import Organization
from server.model.group import Group
from server.model.user import User
from server.model.permission import ReScopeRole, ReUserRole, Role, Scope
from server.utils.response_util import RET
from server.utils.db import Insert, Delete, collect_sql_error


class RoleHandler:
    @staticmethod
    @collect_sql_error
    def get(role_id):
        role = Role.query.filter_by(id=role_id).first()
        if not role:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="The role is not exist")
        
        return_data = role.to_json()

        scopes = []

        for re in role.re_scope_role:
            scope = Scope.query.filter_by(id=re.scope_id).first()
            scopes.append(scope.to_json())
        
        return_data.update({"scopes": scopes})

        users = []

        for re in role.re_user_role:
            user = User.query.filter_by(gitee_id=re.user_id).first()
            users.append(user.to_dict())

        return_data.update({"users": users})

        return jsonify(error_code=RET.OK, error_msg="OK", data=return_data)


    @staticmethod
    @collect_sql_error
    def get_all(query):
        filter_params = []
        for key, value in query.dict().items():
            if not value:
                continue
            if key == 'name':
                filter_params.append(Role.name.like(f'%{value}%'))
            if key == 'description':
                filter_params.append(Role.description.like(f'%{value}%'))

        roles = Role.query.filter(*filter_params).all()
        return_data = [role.to_json() for role in roles]

        return  jsonify(error_code=RET.OK, error_msg="OK", data=return_data)
    
    @staticmethod
    @collect_sql_error
    def create(body):
        _body = body.__dict__

        _relation = None
        _role = None
        if _body["type"] == "group":
            _relation = Group.query.filter_by(
                id=_body["group_id"]
            ).first()
            _role = Role.query.filter_by(
                name=_body["name"],
                group_id=_body["group_id"],
                type="group"
            ).first()
        if _body["type"] == "org":
            _relation = Organization.query.filter_by(
                id=_body["org_id"]
            ).first()
            _role = Role.query.filter_by(
                name=_body["name"],
                org_id=_body["org_id"],
                type="org"
            ).first()
        if _body["type"] == "public":
            _role = Role.query.filter_by(
                name=_body["name"],
                type="public"
            ).first()

        if not _relation and _body["type"] != "public":
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="Group/Organization has not been exist")

        if _role is not None:
            return jsonify(error_code=RET.DATA_EXIST_ERR, error_msg="This role is already exist")

        _ = Insert(Role, _body).insert_id(Role, '/role')
        return jsonify(error_code=RET.OK, error_msg="OK")

    @staticmethod
    @collect_sql_error
    def delete(role_id):
        role = Role.query.filter_by(id=role_id).first()
        if not role:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="The role to delete is not exist")
        
        db.session.delete(role)
        db.session.commit()

        return jsonify(error_code=RET.OK, error_msg="OK")
        
    @staticmethod
    @collect_sql_error
    def update(role_id, body):
        role = Role.query.filter_by(id=role_id).first()
        if not role:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="The role to delete is not exist")

        role.name = body.name

        role.add_update()

        return jsonify(error_code=RET.OK, error_msg="OK")


class ScopeHandler:
    @staticmethod
    @collect_sql_error
    def get_all(query):
        filter_params = []
        for key, value in query.dict().items():
            if not value:
                continue
            if key == 'alias':
                filter_params.append(Scope.alias.like(f'%{value}%'))
            if key == 'uri':
                filter_params.append(Scope.uri.like(f'%{value}%'))
            if key == 'act':
                filter_params.append(Scope.act == value)
            if key == 'eft':
                filter_params.append(Scope.eft == value)

        scopes = Scope.query.filter(*filter_params).all()
        return_data = [scope.to_json() for scope in scopes]

        return  jsonify(error_code=RET.OK, error_msg="OK", data=return_data)
    
    @staticmethod
    @collect_sql_error
    def create(body):
        _ = Insert(Scope, body.__dict__).insert_id(Scope, '/scope')
        return jsonify(error_code=RET.OK, error_msg="OK")

    @staticmethod
    @collect_sql_error
    def delete(role_id):
        scope = Scope.query.filter_by(id=role_id).first()
        if not scope:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="The scope to delete is not exist")
        
        db.session.delete(scope)
        db.session.commit()

        return jsonify(error_code=RET.OK, error_msg="OK")
        
    @staticmethod
    @collect_sql_error
    def update(role_id, body):
        scope = Scope.query.filter_by(id=role_id).first()
        if not scope:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="The scope to delete is not exist")

        scope.alias = body.alias
        scope.uri = body.uri
        scope.act = body.act
        scope.eft = body.eft

        scope.add_update()

        return jsonify(error_code=RET.OK, error_msg="OK")


class BindingHandler:  
    @staticmethod
    @collect_sql_error
    def bind_scope_role(body):
        _scope = Scope.query.filter_by(id=body.scope_id).first()
        _role = Role.query.filter_by(id=body.role_id).first()

        if not _scope or not _role:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="Scope/Role has not been exist")

        return Insert(ReScopeRole, body.__dict__).single()

    @staticmethod
    @collect_sql_error
    def bind_user_role(body):
        _user = User.query.filter_by(gitee_id=body.user_id).first()
        _role = Role.query.filter_by(id=body.role_id).first()

        if not _user or not _role:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="User/Role has not been exist")

        return Insert(ReUserRole, body.__dict__).single()


class RoleLimitedHandler:
    def __init__(self, type='public', org_id=None, group_id=None, role_id=None):
        self.role_id = None
        
        _role = Role.query.filter_by(id=role_id).first()
        if _role and _role.type == type and _role.org_id == org_id and _role.group_id == group_id:
            self.role_id = _role.id


class UserRoleLimitedHandler(RoleLimitedHandler):
    def __init__(self, type='public', org_id=None, group_id=None, body=None):
        super().__init__(type, org_id, group_id, body.role_id)
        self.user_id = None
        _user = User.query.filter_by(gitee_id=body.user_id).first()
        if _user:
            self.user_id = _user.gitee_id

    def bind_user(self):
        if not self.role_id or not self.user_id:
            return jsonify(error_code=RET.VERIFY_ERR, error_msg="permission denied")
        
        return Insert(
            ReUserRole, 
            {
                "user_id": self.user_id, 
                "role_id": self.role_id
            }
        ).single()

    def unbind_user(self):
        if not self.role_id or not self.user_id:
            return jsonify(error_code=RET.VERIFY_ERR, error_msg="permission denied")
        
        re = ReUserRole.query.filter_by(role_id=self.role_id, user_id=self.user_id).first()
        if not re:
            return jsonify(error_code=RET.DATA_EXIST_ERR, error_msg="This Binding is already not exist")

        return Delete(
            ReUserRole,
            {
                "id": re.id,
            }
        ).single()


class ScopeRoleLimitedHandler(RoleLimitedHandler):
    def __init__(self, type='public', org_id=None, group_id=None, body=None):
        super().__init__(type, org_id, group_id, body.role_id)
        self.scope_id = None
        _scope = Scope.query.filter_by(id=body.scope_id).first()
        if _scope:
            self.scope_id = _scope.id

    def bind_scope(self):
        if not self.role_id or not self.scope_id:
            return jsonify(error_code=RET.VERIFY_ERR, error_msg="permission denied")
        
        return Insert(
            ReScopeRole, 
            {
                "scope_id": self.scope_id, 
                "role_id": self.role_id
            }
        ).single()

    def unbind_scope(self):
        if not self.role_id or not self.scope_id:
            return jsonify(error_code=RET.VERIFY_ERR, error_msg="permission denied")
        
        re = ReScopeRole.query.filter_by(role_id=self.role_id, scope_id=self.scope_id).first()
        if not re:
            return jsonify(error_code=RET.NO_DATA_ERR, error_msg="This Binding is already not exist")

        return Delete(
            ReScopeRole,
            {
                "id": re.id,
            }
        ).single()