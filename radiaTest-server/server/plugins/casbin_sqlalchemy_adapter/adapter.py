from typing import List

from casbin import persist
from sqlalchemy import or_

from server import db
from server.model.casbin_rule import CasbinRule


class Filter:
    ptype = []
    v0 = []
    v1 = []
    v2 = []
    v3 = []
    v4 = []
    v5 = []


class Adapter(persist.Adapter, persist.adapters.UpdateAdapter):
    """the interface for Casbin adapters."""

    def __init__(self, filtered=False):
        self._filtered = filtered

    def load_policy(self, model):
        """loads all policy rules from the storage."""
        lines = CasbinRule.query.all()
        for line in lines:
            persist.load_policy_line(str(line), model)

    def is_filtered(self):
        return self._filtered

    def load_filtered_policy(self, model, filter) -> None:
        """loads all policy rules from the storage."""
        query = CasbinRule.query
        filters = self.filter_query(query, filter)
        filters = filters.all()

        for line in filters:
            persist.load_policy_line(str(line), model)
        self._filtered = True

    def filter_query(self, querydb, filter):
        for attr in ("ptype", "v0", "v1", "v2", "v3", "v4", "v5"):
            if len(getattr(filter, attr)) > 0:
                querydb = querydb.filter(
                    getattr(CasbinRule, attr).in_(getattr(filter, attr))
                )
        return querydb.order_by(CasbinRule.id)

    def _save_policy_line(self, ptype, rule):
        line = CasbinRule(ptype=ptype)
        for i, v in enumerate(rule):
            setattr(line, "v{}".format(i), v)
        line.add_update()

    def save_policy(self, model):
        """saves all policy rules to the storage."""
        query = CasbinRule.query
        query.delete()
        db.session.commit()

        for sec in ["p", "g"]:
            if sec not in model.model.keys():
                continue
            for ptype, ast in model.model[sec].items():
                for rule in ast.policy:
                    self._save_policy_line(ptype, rule)
        return True

    def add_policy(self, sec, ptype, rule):
        """adds a policy rule to the storage."""
        self._save_policy_line(ptype, rule)

    def add_policies(self, sec, ptype, rules):
        """adds a policy rules to the storage."""
        for rule in rules:
            self._save_policy_line(ptype, rule)

    def remove_policy(self, sec, ptype, rule):
        """removes a policy rule from the storage."""
        query = CasbinRule.query
        query = query.filter(CasbinRule.ptype == ptype)
        for i, v in enumerate(rule):
            query = query.filter(getattr(CasbinRule, "v{}".format(i)) == v)

        r = query.delete()
        db.session.commit()
        return True if r > 0 else False

    def remove_policies(self, sec, ptype, rules):
        """remove policy rules from the storage."""
        if not rules:
            return
        
        query = CasbinRule.query
        query = query.filter(CasbinRule.ptype == ptype)
        rules = zip(*rules)
        for i, rule in enumerate(rules):
            query = query.filter(
                or_(getattr(CasbinRule, "v{}".format(i)) == v for v in rule)
            )

        query.delete()
        db.session.commit()

    def remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        """removes policy rules that match the filter from the storage.
        This is part of the Auto-Save feature.
        """
  
        query = CasbinRule.query.filter(CasbinRule.ptype == ptype)

        if not (0 <= field_index <= 5):
            return False
        if not (1 <= field_index + len(field_values) <= 6):
            return False
        for i, v in enumerate(field_values):
            if v != "":
                v_value = getattr(CasbinRule, "v{}".format(field_index + i))
                query = query.filter(v_value == v)
        r = query.delete()
        db.session.commit()

        return True if r > 0 else False

    def update_policy(
        self, sec: str, ptype: str, old_rule: List[str], new_rule: List[str]
    ) -> None:
        """
        Update the old_rule with the new_rule in the database (storage).

        :param sec: section type
        :param ptype: policy type
        :param old_rule: the old rule that needs to be modified
        :param new_rule: the new rule to replace the old rule

        :return: None
        """

        query = CasbinRule.query.filter(CasbinRule.ptype == ptype)

        # locate the old rule
        for index, value in enumerate(old_rule):
            v_value = getattr(CasbinRule, "v{}".format(index))
            query = query.filter(v_value == value)

        # need the length of the longest_rule to perform overwrite
        longest_rule = old_rule if len(old_rule) > len(new_rule) else new_rule
        old_rule_line = query.one()

        # overwrite the old rule with the new rule
        for index in range(len(longest_rule)):
            if index < len(new_rule):
                exec(f"old_rule_line.v{index} = new_rule[{index}]")
            else:
                exec(f"old_rule_line.v{index} = None")

    def update_policies(
        self,
        sec: str,
        ptype: str,
        old_rules: List[
            List[str],
        ],
        new_rules: List[
            List[str],
        ],
    ) -> None:
        """
        Update the old_rules with the new_rules in the database (storage).

        :param sec: section type
        :param ptype: policy type
        :param old_rules: the old rules that need to be modified
        :param new_rules: the new rules to replace the old rules

        :return: None
        """
        for i in range(len(old_rules)):
            self.update_policy(sec, ptype, old_rules[i], new_rules[i])
