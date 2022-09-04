from math import floor
import redis
from sqlalchemy.dialects.mysql import LONGTEXT

from server import db
from server.model import BaseModel
from server.model.milestone import IssueSolvedRate, Milestone
from server.utils.at_utils import OpenqaATStatistic


class QualityBoard(BaseModel, db.Model):
    __tablename__ = "qualityboard"

    id = db.Column(db.Integer(), primary_key=True)
    iteration_version = db.Column(db.String(256), nullable=True)
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"), nullable=True)

    feature_list = db.relationship('FeatureList', backref="qualityboard", cascade="all, delete")

    def get_current_version(self):
        vers = None
        if len(self.iteration_version) > 0:
            vers = self.iteration_version.split("->")[-1]
        return vers

    def get_milestones(self):
        milestones = dict()
        if len(self.iteration_version) > 0:
            mids = self.iteration_version.split("->")
            for _id in mids:
                milestone = Milestone.query.filter_by(id=_id).first()
                milestones.update({_id: milestone.to_json()})
        return milestones

    def to_json(self):
        current_milestone_id = self.get_current_version()
        _isr = IssueSolvedRate.query.filter_by(
            milestone_id=current_milestone_id
        ).first()

        return {
            "id": self.id,
            "product_id": self.product_id,
            "iteration_version": self.iteration_version,
            "milestones": self.get_milestones(),
            "current_milestone_id": current_milestone_id,
            "current_milestone_issue_solved_rate": _isr.to_json() if _isr else {},
        }


class Checklist(db.Model, BaseModel):
    __tablename__ = "checklist"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    check_item = db.Column(db.String(50), nullable=False, unique=True)
    baseline = db.Column(db.String(50))
    rounds = db.Column(db.String(128), default=False)
    lts = db.Column(db.Boolean(), default=False)
    lts_spx = db.Column(db.Boolean(), default=False)
    innovation = db.Column(db.Boolean(), default=False)

    def to_json(self):
        return {
            'id': self.id,
            'check_item': self.check_item,
            'baseline': self.baseline,
            'rounds': self.rounds,
            'lts': self.lts,
            'lts_spx': self.lts_spx,
            'innovation': self.innovation,
            'create_time': self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            'update_time': self.update_time.strftime("%Y-%m-%d %H:%M:%S")
        }


class DailyBuild(db.Model, BaseModel):
    __tablename__ = "dailybuild"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    completion = db.Column(db.Integer(), nullable=False, default=0)
    detail = db.Column(LONGTEXT(), nullable=True)
    at_passed = db.Column(db.Boolean(), default=False)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    weekly_health_id = db.Column(db.Integer(), db.ForeignKey("weekly_health.id"))

    def set_at_passed(self, pool, arches):
        _client = redis.StrictRedis(connection_pool=pool)
        at_statistic = OpenqaATStatistic(
            arches=arches,
            product=f"{self.product.name}-{self.product.version}",
            build=self.name,
            redis_client=_client
        ).group_overview
        self.at_passed = (
            (
                at_statistic.get("success") == at_statistic.get("total")
            ) and at_statistic.get("total") != 0
        )
        self.add_update()

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "completion": self.completion,
            "product_id": self.product_id
        }
    
    def to_health_json(self, pool, arches):
        self.set_at_passed(pool, arches)
        return {
            "id": self.id,
            "name": self.name,
            "build_passed": self.completion == 100,
            "at_passed": self.at_passed,
        }


class WeeklyHealth(db.Model, BaseModel):
    __tablename__ = "weekly_health"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    start_time = db.Column(db.String(50), nullable=False)
    end_time = db.Column(db.String(50), nullable=False)

    daily_records = db.relationship('DailyBuild')
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    def get_statistic(self, pool, arches):
        build_record_total = len(self.daily_records)

        build_record_success = 0
        at_record_success = 0
        for record in self.daily_records:
            record.set_at_passed(pool, arches)
            if record.completion == 100:
                build_record_success += 1
            at_record_success += record.at_passed
        
        return {
            "health_rate": floor(
                at_record_success / build_record_total * 100
            ) if build_record_total else None,
            "at_passed_rate": floor(
                at_record_success / build_record_success * 100
            ) if build_record_success else None,
            "build_passed_rate": floor(
                build_record_success / build_record_total * 100
            ) if build_record_total else None,
        }

    def to_json(self, pool, arches):
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            **self.get_statistic(pool, arches)
        }


class FeatureList(db.Model, BaseModel):
    __tablename__ = "feature_list"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    no = db.Column(db.String(50), nullable=False, unique=True)
    url = db.Column(db.String(512))
    feature = db.Column(db.String(512), nullable=False)
    sig = db.Column(db.String(50))
    owner = db.Column(LONGTEXT())
    release_to = db.Column(db.String(50)) 
    pkgs = db.Column(LONGTEXT())
    is_new = db.Column(db.Boolean(), nullable=False, default=True)
    done = db.Column(db.Boolean(), nullable=False, default=False)
    
    qualityboard_id = db.Column(db.Integer(), db.ForeignKey("qualityboard.id"))
    task_id = db.Column(db.Integer(), db.ForeignKey("task.id"))

    def to_json(self):
        return {
            "id": self.id,
            "no": self.no,
            "url": self.url,
            "feature": self.feature,
            "sig": None if not self.sig else self.sig.split(' '),
            "owner": None if not self.owner else self.owner.split(' '),
            "release_to": self.release_to,
            "pkgs": None if not self.pkgs else self.pkgs.split(','),
            "task_status": self.task.task_status.name if self.task else None,
            "is_new": self.is_new,
            "done": self.done,
        }


class RpmCompare(db.Model, BaseModel):
    __tablename__ = "rpm_compare"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    arch = db.Column(db.String(50), nullable=False)
    rpm_comparee = db.Column(db.String(128))
    rpm_comparer = db.Column(db.String(128))
    compare_result = db.Column(db.String(50))

    milestone_group_id = db.Column(
        db.Integer(), db.ForeignKey('milestone_group.id', ondelete="CASCADE"), nullable=False
    )

    def to_json(self):
        return {
            "id": self.id,
            "rpm_comparee": self.rpm_comparee,
            "rpm_comparer": self.rpm_comparer,
            "compare_result": self.compare_result,
        }