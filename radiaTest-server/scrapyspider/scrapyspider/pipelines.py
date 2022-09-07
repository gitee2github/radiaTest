# Copyright (c) [2022] Huawei Technologies Co.,Ltd.ALL rights reserved.
# You can use it according to the terms and conditions of the Mulan PSL v2.
#          http://license.coscl.org.cn/MulanPSL2
# THIS PROGRAM IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# Part of codes were generated by scrapy startproject
####################################
# @Author  : Ethan-Zhang
# @email   : ethanzhang55@outlook.com
# @Date    : 2022/08/10 14:13:00
# @License : Mulan PSL v2
#####################################

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import configparser
from datetime import datetime
import re
import os
import subprocess
import time
from pathlib import Path
import pytz

import redis

from scrapyspider.items import (
    OpeneulerPkgsListItem, 
    OpenqaHomeItem, 
    OpenqaGroupOverviewItem, 
    OpenqaTestsOverviewItem
)


class ScrapyspiderPipeline:
    def process_item(self, item, spider):
        return item


class FilePipeline:
    def open_spider(self, spider):
        server_config_ini = Path(spider.settings.get("SERVER_INI_PATH"))
        cfg = configparser.ConfigParser()
        cfg.read(server_config_ini)

        self.pkglist_storage_path = cfg.get("pkglist", "PRODUCT_PKGLIST_PATH")
        if not os.path.isdir(self.pkglist_storage_path):
            os.mkdir(self.pkglist_storage_path)

        self.timestamp = datetime.now(tz=pytz.timezone('Asia/Shanghai')).strftime('%Y%m%d%H%M%S')

    def process_item(self, item, spider):
        if isinstance(item, OpeneulerPkgsListItem):
            self.product = item["product"]
            self.build = item["build"]

            exitcode, output = subprocess.getstatusoutput(
                f"echo {item['rpm_file_name']} >> {self.pkglist_storage_path}/{self.build}-{self.timestamp}.pkgs"
            )
            if exitcode != 0:
                raise RuntimeError(output)

    def close_spider(self, spider):
        pattern = r'^rc([1-9])_+'
        result = re.match(pattern, self.build)
        if result:
            if os.path.isfile(f"{self.pkglist_storage_path}/{self.product}-round-{result.group(1)}.pkgs"):
                os.remove(f"{self.pkglist_storage_path}/{self.product}-round-{result.group(1)}.pkgs")
            os.rename(
                f"{self.pkglist_storage_path}/{self.build}-{self.timestamp}.pkgs",
                f"{self.pkglist_storage_path}/{self.product}-round-{result.group(1)}.pkgs"
            )
        else:
            if os.path.isfile(f"{self.pkglist_storage_path}/{self.product}.pkgs"):
                os.remove(f"{self.pkglist_storage_path}/{self.product}.pkgs")
            os.rename(
                f"{self.pkglist_storage_path}/{self.build}-{self.timestamp}.pkgs",
                f"{self.pkglist_storage_path}/{self.product}.pkgs"
            )


class RedisPipeline:
    def open_spider(self, spider):
        server_config_ini = Path(spider.settings.get("SERVER_INI_PATH"))
        cfg = configparser.ConfigParser()
        cfg.read(server_config_ini)

        host = cfg.get("redis", "REDIS_HOST")
        port = cfg.get("redis", "REDIS_PORT")
        try:
            db_index = int(cfg.get("redis", "REDIS_SCRAPYSPIDER_DB"))
        except ValueError:
            db_index = cfg.get("redis", "REDIS_DB")
        db_psd = cfg.get("redis", "REDIS_SECRET")

        self.db_conn = redis.StrictRedis(host=host, port=port, db=db_index, password=db_psd)

    def process_item(self, item, spider):
        if isinstance(item, OpenqaHomeItem):
            self.db_conn.set(
                "{}_group_overview_url".format(
                    item["product_name"]
                ), 
                item["group_overview_url"]
            )
            return item
        
        elif isinstance(item, OpenqaGroupOverviewItem):
            _build_time_array = time.strptime(item["build_time"], "%Y-%m-%dT%H:%M:%SZ")
            _build_time_stamp = int(time.mktime(_build_time_array))

            self.db_conn.zadd(
                item["product_name"],
                {
                    item["build_name"]: _build_time_stamp
                }
            )

            self.db_conn.set(
                "{}_{}_tests_overview_url".format(
                    item["product_name"],
                    item["build_name"]
                ),
                item["build_tests_url"]
            )
        
        elif isinstance(item, OpenqaTestsOverviewItem):
            _key = "{}_{}".format(
                item["product_build"],
                item["test"],
            )

            self.db_conn.hset(_key, "aarch64_res_status", item["aarch64_res_status"])
            self.db_conn.hset(_key, "aarch64_res_log", item["aarch64_res_log"])
            self.db_conn.hset(_key, "aarch64_failedmodule_name", item["aarch64_failedmodule_name"])
            self.db_conn.hset(_key, "aarch64_failedmodule_log", item["aarch64_failedmodule_log"])

            self.db_conn.hset(_key, "x86_64_res_status", item["x86_64_res_status"])
            self.db_conn.hset(_key, "x86_64_res_log", item["x86_64_res_log"])
            self.db_conn.hset(_key, "x86_64_failedmodule_name", item["x86_64_failedmodule_name"])
            self.db_conn.hset(_key, "x86_64_failedmodule_log", item["x86_64_failedmodule_log"])
            

    def close_spider(self, spider):
        self.db_conn.connection_pool.disconnect()