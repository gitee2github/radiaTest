import time
import shlex
import requests
import json
from subprocess import getoutput, getstatusoutput

from celeryservice import celeryconfig
from . import TaskHandlerBase
from worker.utils.bash import (
    get_bridge_source,
    get_network_source,
    install_base,
    rm_disk_image,
    domain_cli,
    domain_state,
    undefine_domain,
)


config = celeryconfig.__dict__


class VmachineBase(TaskHandlerBase):
    def __init__(self, logger, body):
        self._body = body
        self._user = body["user_id"] if body.get("user_id") else "unknown"
        self._vmachine = body["vmachine_name"] if body.get("vmachine_name") else "unknown"
        super().__init__(logger)
    
    def delete_vmachine(self):
        _ = requests.delete(
            url="{}://{}:{}/api/v1/vmachine".format(
                config.get("PROTOCOL"),
                config.get("SERVER_IP"),
                config.get("SERVER_PORT"),
            ),
            data={
                "id": [self._body["id"]],
            },
            headers=config.get("HEADERS")
        )

    def update_vmachine(self, body):
        _ = requests.put(
            url="{}://{}:{}/api/v1/vmachine/callback".format(
                config.get("PROTOCOL"),
                config.get("SERVER_IP"),
                config.get("SERVER_PORT"),
            ),
            data=json.dumps(body),
            headers=config.get("HEADERS")
        )


class InstallVmachine(VmachineBase):
    def kickstart(self, promise):
        self.logger.info(
            "user {0} attempt to create vmachine by autoinstall from {1}".format(
                self._user,
                self._body["location"]
            )
        )

        promise.update_state(
            state="CREATING",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
                
            },
        )

        source = getoutput(get_network_source())
        if not source:
            output = "network mode virtual bridge is not configured"
            self.logger.error(
                "user {0} fail to create vmachine by autoinstall from {1}, because {2}".format(
                    self._user,
                    self._body["location"],
                    output
                )
            )
            self.delete_vmachine()
            raise RuntimeError(output)

        exitcode, output = getstatusoutput(
            "qemu-img create -f qcow2 {}/{}.qcow2 {}G".format(
                shlex.quote(config.get("STORAGE_POOL").replace("/$", "")),
                shlex.quote(self._body.get("name")),
                shlex.quote(str(self._body.get("capacity"))),
            )
        )
        if exitcode:
            self.logger.error(
                "user {0} fail to create vmachine by autoinstall from {1}, because {2}".format(
                    self._user,
                    self._body["location"],
                    output
                )
            )
            self.delete_vmachine()
            raise RuntimeError(output)

        self.next_period()
        promise.update_state(
            state="INSTALLING",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
                
            },
        )

        cmd = " {} --network network={} --location {} --extra-args ks={}".format(
            install_base(self._body, config),
            source,
            shlex.quote(self._body.get("location")),
            shlex.quote(self._body.get("ks")),
        )
        exitcode, output = getstatusoutput(cmd)

        if exitcode:
            self.logger.error(
                "user {0} fail to create vmachine by autoinstall from {1}, because {2}".format(
                    self._user,
                    self._body["location"],
                    output
                )
            )
            self.delete_vmachine()
            raise RuntimeError(output)

        self.next_period()
        promise.update_state(
            state="STARTING",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
                
            },
        )

        for _ in range(900):
            exitcode = getstatusoutput(
                "export LANG=en_US.utf-8 ; test \"$(eval echo $(virsh list --all | grep '{}' | awk -F '{} *' ".format(
                shlex.quote(self._body.get("name")), shlex.quote(self._body.get("name"))
                )
                + "'{print $NF}'))\" == 'shut off'"
                )[0]
            if exitcode == 0:
                exitcode, output = getstatusoutput(
                    "virsh start {}".format(shlex.quote(self._body.get("name")))
                )
                break
            time.sleep(1)

        exitcode, output = getstatusoutput(
            "export LANG=en_US.utf-8 ; eval echo $(virsh list --all | grep '{}' ".format(
                shlex.quote(self._body.get("name"))
            )
            + " | awk -F '  ' '{print $NF}')"
        )

        self.next_period()
        promise.update_state(
            state="DONE",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
                
            },
        )

        self.logger.error(
            "user {0} finish to create vmachine by autoinstall from {1}".format(
                self._user,
                self._body["location"],
            )
        )

        self._body.update(
            {
                "mac": getoutput(
                    "virsh dumpxml %s | grep -Pzo  \"<interface type='bridge'>[\s\S] *<mac address.*\" |grep -Pzo '<mac address.*' | awk -F\\' '{print $2}' | head -1"
                    % self._body.get("name")
                ).strip(),
                "status": output,
                "vnc_port": domain_cli("vncdisplay", self._body.get("name"))[1]
                .strip("\n")
                .split(":")[-1],
            }
        )

        self.update_vmachine(self._body)

    def _import(self, promise):
        self.logger.info(
            "user {0} attempt to create vmachine imported from {1}".format(
                self._user,
                self._body["url"],
            )
        )
        
        promise.update_state(
            state="DOWNLOADING",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
            },
        )

        self._body.update(
            {"source": config.get("NETWORK_INTERFACE_SOURCE")}
        )

        exitcode, output = getstatusoutput(
            "sudo wget -nv -c {} -O {}/{}.qcow2 2>&1".format(
                shlex.quote(self._body.get("url")),
                shlex.quote(config.get("STORAGE_POOL")),
                shlex.quote(self._body.get("name")),
            )
        )
        if exitcode:
            self.logger.error(
                "user {0} fail to create vmachine imported from {1}, because {2}".format(
                    self._user,
                    self._body["url"],
                    output,
                )
            )
            rm_disk_image(self._body.get("name"))
            raise output

        self.next_period()
        promise.update_state(
            state="IMPORTING",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
            },
        )

        exitcode, output = getstatusoutput(
            "{} --import --noreboot".format(install_base(self._body, config))
        )
        if exitcode:
            self.logger.error(
                "user {0} fail to create vmachine imported from {1}, because {2}".format(
                    self._user,
                    self._body["url"],
                    output,
                )
            )
            rm_disk_image(self._body.get("name"))
            self.delete_vmachine()
            raise RuntimeError(output)

        self.next_period()
        promise.update_state(
            state="STARTING",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
            },
        )

        exitcode, output = domain_cli("start", self._body.get("name"))
        if exitcode:
            exitcode, result = undefine_domain(self._body.get("name"))
            if not exitcode:
                self.logger.error(
                "user {0} fail to create vmachine imported from {1}, because {2}".format(
                        self._user,
                        self._body["url"],
                        output + "&" + result,
                    )
                )
                self.delete_vmachine()
                raise RuntimeError(output + "&" + result)
            self.logger.error(
                "user {0} fail to create vmachine imported from {1}, because {2}".format(
                    self._user,
                    self._body["url"],
                    output,
                )
            )
            self.delete_vmachine()
            raise RuntimeError(output)

        self._body.update(
            {
                "mac": getoutput(
                    "virsh dumpxml %s | grep -Pzo  \"<interface type='bridge'>[\s\S] *<mac address.*\" |grep -Pzo '<mac address.*' | awk -F\\' '{print $2}' | head -1"
                    % self._body.get("name")
                ).strip(),
                "status": "running",
                "vnc_port": domain_cli(
                    "vncdisplay", self._body.get("name"))[1]
                    .strip("\n")
                    .split(":"
                )[-1],
            }
        )

        self.update_vmachine(self._body)

        self.logger.info(
            "user {0} finish to create vmachine imported from {1}".format(
                self._user,
                self._body["url"],
            )
        )

        self.next_period()
        promise.update_state(
            state="DONE",
            meta={
                "start_time": self.start_time,
                "running_time": self.running_time,
                
            },
        )

    def cd_rom(self, promise):
        # TODO @lemon-higgins
        # nfs + fstab 实现
        pass
