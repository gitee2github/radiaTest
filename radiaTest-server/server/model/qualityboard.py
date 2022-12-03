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
    released = db.Column(db.Boolean(), default=False)
    product_id = db.Column(
        db.Integer(), db.ForeignKey("product.id"), nullable=True
    )

    feature_list = db.relationship(
        'FeatureList', backref="qualityboard", cascade="all, delete"
    )

    def get_round_milestones(self):
        milestones = dict()
        if len(self.iteration_version) > 0:
            round_id = self.iteration_version.split("->")[-1]
            _milestones = Milestone.query.filter_by(round_id=round_id).all()
            for _m in _milestones:
                milestones.update({str(_m.id): _m.to_json()})
        return milestones

    def get_current_round(self):
        _round = None
        if len(self.iteration_version) > 0:
            _round = self.iteration_version.split("->")[-1]
        return _round

    def get_rounds(self):
        rounds = dict()
        if len(self.iteration_version) > 0:
            rids = self.iteration_version.split("->")
            for _id in rids:
                _round = Round.query.filter_by(id=_id).first()
                rounds.update({_id: _round.to_json()})
        return rounds

    def to_json(self):
        current_round_id = self.get_current_round()
        _isr = IssueSolvedRate.query.filter_by(
            round_id=current_round_id, type="round"
        ).first()

        return {
            "id": self.id,
            "product_id": self.product_id,
            "iteration_version": self.iteration_version,
            "rounds": self.get_rounds(),
            "released": self.released,
            "current_round_id": current_round_id,
            "milestones": self.get_round_milestones(),
            "current_round_issue_solved_rate": _isr.to_json() if _isr else {},
        }


class Checklist(db.Model, BaseModel):
    __tablename__ = "checklist"
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    baseline = db.Column(db.String(255))
    rounds = db.Column(db.String(128))
    operation = db.Column(db.String(255))
    checkitem_id = db.Column(db.Integer(), db.ForeignKey("checkitem.id"))
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    def to_json(self):
        ci = CheckItem.query.filter_by(id=self.checkitem_id).first()
        return {
            'id': self.id,
            'check_item': ci.title if ci else None,
            'baseline': self.baseline,
            'rounds': self.rounds,
            "operation": self.operation,
            "checkitem_id": self.checkitem_id,
            "product_id": self.product_id,
            'create_time': self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            'update_time': self.update_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def to_json2(self):
        ci = CheckItem.query.filter_by(id=self.checkitem_id).first()
        checkitem_name = ci.title if ci else None
        data = []
        if self.rounds.count("1") == 0:
            item = {
                'id': self.id,
                'check_item': checkitem_name,
                'baseline': self.baseline.split(",")[0],
                'rounds': self.rounds,
                "operation": self.operation.split(",")[0],
                "checkitem_id": self.checkitem_id,
                "product_id": self.product_id,
            }
            data.append(item)
            return data
        idx = 0
        r_len = len(self.rounds)
        if r_len == 1:
            item = {
                'id': self.id,
                'check_item': checkitem_name,
                'baseline': self.baseline,
                'rounds': self.rounds,
                "operation": self.operation,
                "checkitem_id": self.checkitem_id,
                "product_id": self.product_id,
            }
            data.append(item)
            return data
        idx = 0
        t_dict = dict()
        baseline = self.baseline.split(",")
        operation = self.operation.split(",")
        for _r in self.rounds:
            tstr = baseline[idx] + "," + operation[idx]
            if tstr == ",":
                idx += 1
                continue
            if _r == "0":
                idx += 1
                if not t_dict.get(tstr):
                    t_dict.update({
                        tstr: ""
                    })
                continue
            if t_dict.get(tstr):
                t_dict.update({
                    tstr: t_dict.get(tstr) + "," + str(idx)
                })
            else:
                t_dict.update({
                    tstr: str(idx)
                })
            idx += 1
        for k in t_dict.keys():
            t_idxs = t_dict.get(k).split(",")
            t_rounds = ["0"] * len(self.rounds)
            for t_idx in t_idxs:
                if t_idx == "":
                    break
                t_rounds[int(t_idx)] = "1"
            
            item = {
                'id': self.id,
                'check_item': checkitem_name,
                'baseline': k.split(",")[0],
                'rounds': "".join(t_rounds),
                "operation": k.split(",")[1],
                "checkitem_id": self.checkitem_id,
                "product_id": self.product_id,
            }
            data.append(item)
        return data


class CheckItem(db.Model, BaseModel):
    __tablename__ = "checkitem"
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    field_name = db.Column(db.String(50), nullable=False, unique=True)
    title = db.Column(db.String(50), nullable=False, unique=True)
    checklist = db.relationship(
        'Checklist', backref="checkitem"
    )

    def to_json(self):
        return {
            'id': self.id,
            'field_name': self.field_name,
            'title': self.title,
        }


class DailyBuild(db.Model, BaseModel):
    __tablename__ = "dailybuild"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    completion = db.Column(db.Integer(), nullable=False, default=0)
    detail = db.Column(LONGTEXT(), nullable=True)
    at_passed = db.Column(db.Boolean(), default=False)

    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))
    weekly_health_id = db.Column(
        db.Integer(), db.ForeignKey("weekly_health.id")
    )

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
    status = db.Column(db.String(50))
    feature = db.Column(db.String(512), nullable=False)
    sig = db.Column(db.String(50))
    owner = db.Column(LONGTEXT())
    release_to = db.Column(db.String(50))
    pkgs = db.Column(LONGTEXT())
    is_new = db.Column(db.Boolean(), nullable=False, default=True)

    qualityboard_id = db.Column(db.Integer(), db.ForeignKey("qualityboard.id"))
    task_id = db.Column(db.Integer(), db.ForeignKey("task.id"))

    def to_json(self):
        return {
            "id": self.id,
            "no": self.no,
            "url": self.url,
            "status": self.status,
            "feature": self.feature,
            "sig": None if not self.sig else self.sig.split(' '),
            "owner": None if not self.owner else self.owner.split(' '),
            "release_to": self.release_to,
            "pkgs": None if not self.pkgs else self.pkgs.split(','),
            "task_status": self.task.task_status.name if self.task else None,
            "is_new": self.is_new,
        }


class RpmCompare(db.Model, BaseModel):
    __tablename__ = "rpm_compare"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    repo_path = db.Column(db.String(50), nullable=False)
    arch = db.Column(db.String(50), nullable=False)
    rpm_comparee = db.Column(db.String(128))
    rpm_comparer = db.Column(db.String(128))
    compare_result = db.Column(db.String(50))

    round_group_id = db.Column(
        db.Integer(), db.ForeignKey('round_group.id', ondelete="CASCADE"), nullable=False
    )

    def to_json(self):
        return {
            "id": self.id,
            "rpm_comparee": self.rpm_comparee,
            "rpm_comparer": self.rpm_comparer,
            "compare_result": self.compare_result,
            "repo_path": self.repo_path,
            "arch": self.arch,
        }


class SameRpmCompare(db.Model, BaseModel):
    __tablename__ = "same_rpm_compare"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    repo_path = db.Column(db.String(50), nullable=False)
    rpm_name = db.Column(db.String(50), nullable=False)
    rpm_x86 = db.Column(db.String(128))
    rpm_arm = db.Column(db.String(128))
    compare_result = db.Column(db.String(50))

    round_id = db.Column(
        db.Integer(), db.ForeignKey('round.id', ondelete="CASCADE"), nullable=False
    )

    def to_json(self):
        return {
            "id": self.id,
            "repo_path": self.repo_path,
            "rpm_name": self.rpm_name,
            "rpm_x86": self.rpm_x86,
            "rpm_arm": self.rpm_arm,
            "compare_result": self.compare_result,
            "round_id": self.round_id,
        }


class Round(BaseModel, db.Model):
    __tablename__ = "round"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    round_num = db.Column(db.Integer(), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    default_milestone_id = db.Column(
        db.Integer(), nullable=False,
    )
    built_by_ebs = db.Column(db.Boolean(), nullable=False, default=False)
    buildname = db.Column(db.String(128))

    product_id = db.Column(
        db.Integer(), db.ForeignKey("product.id"),
    )
    milestone = db.relationship('Milestone', backref='round')
    issuesolvedrate = db.relationship('IssueSolvedRate', backref='round')

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "round_num": self.round_num,
            "type": self.type,
            "default_milestone_id": self.default_milestone_id,
            "product_id": self.product_id,
            "built_by_ebs": self.built_by_ebs,
            "buildname": self.buildname,
        }


class RoundGroup(db.Model, BaseModel):
    __tablename__ = "round_group"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    round_1_id = db.Column(
        db.Integer(), db.ForeignKey('round.id', ondelete="CASCADE"), primary_key=True
    )
    round_2_id = db.Column(
        db.Integer(), db.ForeignKey('round.id', ondelete="CASCADE"), primary_key=True
    )


class RpmCheck(db.Model, BaseModel):
    __tablename__ = "rpm_check"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    build_time = db.Column(db.DateTime(), nullable=False)
    all_cnt = db.Column(db.Integer())
    success_cnt = db.Column(db.Integer())
    success_rate = db.Column(db.String(6))
    failed_cnt = db.Column(db.Integer())
    failed_rate = db.Column(db.String(6))
    broken_cnt = db.Column(db.Integer())
    broken_rate = db.Column(db.String(6))
    unresolvable_cnt = db.Column(db.Integer())
    unresolvable_rate = db.Column(db.String(6))
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"))

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "build_time": self.convert_time_format(self.build_time),
            "all_cnt": self.all_cnt,
            "success_cnt": self.success_cnt,
            "success_rate": self.success_rate,
            "failed_cnt": self.failed_cnt,
            "failed_rate": self.failed_rate,
            "broken_cnt": self.broken_cnt,
            "broken_rate": self.broken_rate,
            "unresolvable_cnt": self.unresolvable_cnt,
            "unresolvable_rate": self.unresolvable_rate,
            "product_id": self.product_id,
        }


class RpmCheckDetail(db.Model, BaseModel):
    __tablename__ = "rpm_check_detail"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    package = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum("success", "failed", "broken", "unresolvable"), nullable=False)
    arch = db.Column(db.Enum("x86_64", "aarch64", "noarch"), nullable=False)
    failed_type = db.Column(db.String(20), nullable=False)
    failed_detail = db.Column(db.String(100), nullable=False)
    rpm_check_id = db.Column(db.Integer(), db.ForeignKey("rpm_check.id"))

    def to_json(self):
        return {
            "id": self.id,
            "package": self.package,
            "status": self.status,
            "arch": self.arch,
            "failed_type": self.failed_type,
            "failed_detail": self.failed_detail,
        }