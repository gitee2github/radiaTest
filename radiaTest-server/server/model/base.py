import json
import datetime

from server import db, socketio, redis_client
from server.utils import DateEncoder
from server.utils.redis_util import RedisKey


class Base(object):
    create_time = db.Column(db.DateTime(), default=datetime.datetime.now)
    update_time = db.Column(
        db.DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now
    )

    def add_update(self, table=None, namespace=None, broadcast=False):
        db.session.add(self)
        db.session.commit()
        if table and namespace:
            socketio.emit(
                "update",
                json.dumps([item.to_json() for item in table.query.all()], cls=DateEncoder),
                namespace=namespace,
                broadcast=broadcast,
            )

    def delete(self, table=None, namespace=None, broadcast=False):
        db.session.delete(self)
        db.session.commit()
        if table and namespace:
            socketio.emit(
                "update",
                json.dumps([item.to_json() for item in table.query.all()], cls=DateEncoder),
                namespace=namespace,
                broadcast=broadcast,
            )

    def add_flush_commit(self, table=None, namespace=None, broadcast=False):
        db.session.add(self)
        db.session.flush()
        record_id = None
        if hasattr(self, "id"):
            record_id = self.id
        db.session.commit()

        if table and namespace:
            socketio.emit(
                "update",
                json.dumps([item.to_json() for item in table.query.all()], cls=DateEncoder),
                namespace=namespace,
                broadcast=broadcast,
            )
        
        return record_id


class BaseModel(Base):
    id = db.Column(db.Integer(), primary_key=True)

class PermissionBaseModel(Base):
    permission_type = db.Column(db.Enum(
            "person",  # 个人
            "group",  # 团队
            "org",   # 组织
            "public" #公共
        ),default="person")
