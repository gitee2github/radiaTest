<template>
  <div style="width: 100%; overflow: hidden">
    <n-spin :show="showLoading" stroke="rgba(0, 47, 167, 1)">
      <modal-card :initY="100" :initX="300" title="创建机器组" ref="createModalRef" @validate="submitCreateForm">
        <template #form>
          <n-form
            :label-width="40"
            :model="createMachinesForm"
            :rules="machinesRules"
            label-placement="top"
            ref="machinesFormRef"
          >
            <n-grid :cols="18" :x-gap="24">
              <n-form-item-gi :span="8" label="机器组名" path="name">
                <n-input
                  v-model:value="createMachinesForm.name"
                  placeholder="请输入机器组名"
                  maxlength="25"
                  show-count
                  clearable
                />
              </n-form-item-gi>
              <n-form-item-gi :span="10" label="描述" path="description">
                <n-input v-model:value="createMachinesForm.description" placeholder="请输入描述" />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="网络类型" path="network_type">
                <n-select
                  v-model:value="createMachinesForm.network_type"
                  placeholder="请输入"
                  :options="[
                    { label: 'WAN', value: 'WAN' },
                    { label: 'LAN', value: 'LAN' }
                  ]"
                />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="公网IP地址" path="ip">
                <n-input
                  v-model:value="createMachinesForm.ip"
                  @update:value="changeValue"
                  placeholder="请输入公网IP地址"
                />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="类型" path="permission_type">
                <n-cascader
                  v-model:value="createMachinesForm.permission_type"
                  placeholder="请选择"
                  :disabled="!isCreate"
                  :options="typeOptions"
                  check-strategy="child"
                  remote
                  :on-load="handleLoad"
                />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="messenger IP">
                <n-switch v-model:value="syncMessengerIP">
                  <template #checked> messenger IP同步公网IP </template>
                  <template #unchecked> messenger IP不同步公网IP </template>
                </n-switch>
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="messenger IP" path="messenger_ip">
                <n-input v-model:value="createMachinesForm.messenger_ip" placeholder="请输入messenger IP地址" />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="messenger监听" path="messenger_listen">
                <n-input
                  v-model:value="createMachinesForm.messenger_listen"
                  :input-props="{ min: 0 }"
                  placeholder="请输入"
                  type="number"
                />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="websockify IP">
                <n-switch v-model:value="syncWebsockifyIP">
                  <template #checked> websockify IP同步公网IP </template>
                  <template #unchecked> websockify IP不同步公网IP </template>
                </n-switch>
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="websockify IP" path="websockify_ip">
                <n-input v-model:value="createMachinesForm.websockify_ip" placeholder="请输入websockify IP" />
              </n-form-item-gi>
              <n-form-item-gi :span="6" label="websockify服务端口" path="websockify_listen">
                <n-input
                  v-model:value="createMachinesForm.websockify_listen"
                  placeholder="请输入websockify服务端口"
                  :input-props="{ min: 0 }"
                  type="number"
                />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </template>
      </modal-card>
      <n-layout has-sider>
        <n-layout-sider
          bordered
          content-style="padding: 24px;overflow-y:auto;"
          collapse-mode="transform"
          :collapsed-width="1"
          :width="400"
          show-trigger="arrow-circle"
          :style="{ height: contentHeight + 'px' }"
        >
          <n-alert title="使用须知" type="warning" closable>
            若需要查看资源监控、使用VNC控制台，请<n-button type="info" text @click="handleDownloadCert">下载</n-button
            >并安装根证书批量信任机器组服务，或于机器组节点右键菜单中点击信任单个机器组服务
          </n-alert>
          <n-tree
            block-line
            :data="menuOptions"
            :on-load="handleTreeLoad"
            :node-props="nodeProps"
            :render-prefix="renderPrefix"
            :render-suffix="renderSuffix"
            :selected-keys="selectKey"
            :expanded-keys="expandeds"
            @update:expanded-keys="handleExpandKey"
            @update:selected-keys="handleSelectKey"
          />
          <n-dropdown
            placement="bottom-start"
            trigger="manual"
            :show="showDropdown"
            :options="options"
            :x="x"
            :y="y"
            @select="handleSelect"
            @clickoutside="handleClickoutside"
          />
        </n-layout-sider>
        <n-layout-content
          content-style="padding: 24px;width:100%"
          :style="{
            overflowY: 'auto',
            height: contentHeight + 'px'
          }"
          id="resourcePoolRight"
        >
          <n-tabs
            animated
            type="line"
            @update:value="changeView"
            v-model:value="activeTab"
            size="large"
            style="width: 100%"
          >
            <n-tab name="pmachine" :disabled="!showMachine"> 物理机 </n-tab>
            <n-tab name="vmachine" :disabled="!showMachine"> 虚拟机 </n-tab>
            <n-tab name="docker" :disabled="true"> Docker </n-tab>
          </n-tabs>
          <router-view v-if="showMachine" :key="key" />
          <div v-else style="height: 100%; display: flex; justify-content: center; align-items: center">
            <n-empty description="请选择机器组"> </n-empty>
          </div>
        </n-layout-content>
      </n-layout>
    </n-spin>
  </div>
</template>
<script>
import { modules } from './modules';
import modalCard from '@/components/CRUD/ModalCard.vue';
import extendForm from '@/views/versionManagement/product/modules/createForm.js';

export default {
  components: {
    modalCard
  },
  computed: {
    showMachine() {
      return this.$route.name === 'pmachine' || this.$route.name === 'vmachine';
    },
    key() {
      return window.atob(this.$route.params.machineId);
    }
  },
  unmounted() {
    this.socket.disconnect();
  },
  mounted() {
    this.contentHeight = document.getElementById('homeBody').clientHeight;
    this.contentWidth = document.getElementById('homeBody').clientWidth;
    this.socket.connect();
    this.socket.listen('update', (data) => {
      const updateData = JSON.parse(data);
      if (Array.isArray(updateData)) {
        updateData.forEach((item) => {
          const it = this.menuOptions[0].children.find((i) => i.key === String(item.id));
          if (it) {
            const pxeHeartbeat = new Date(item.pxe_last_heartbeat).getTime() - Date.now();
            const messenger = new Date(item.messenger_last_heartbeat).getTime() - Date.now();
            const dhcp = new Date(item.dhcp_last_heartbeat) - Date.now();
            it.children[1].suffix = this.getTimeDiff(Math.abs(messenger));
            it.children[2].suffix = this.getTimeDiff(Math.abs(pxeHeartbeat));
            it.children[3].suffix = this.getTimeDiff(Math.abs(dhcp));
            it.children[1].color = 'rgba(0,0,0,0)';
            it.children[2].color = 'rgba(0,0,0,0)';
            it.children[3].color = 'rgba(0,0,0,0)';
            setTimeout(() => {
              it.children[1].color = item.messenger_alive ? 'green' : 'red';
              it.children[2].color = item.pxe_alive ? 'green' : 'red';
              it.children[3].color = item.dhcp_alive ? 'green' : 'red';
            }, 50);
          }
        });
      }
    });
    if (this.$route.name === 'resourcePool' && this.expandeds.at(-1) !== 'pool' && this.expandeds.length !== 0) {
      this.$router.push({
        name: this.activeTab,
        params: { machineId: window.btoa(this.expandeds.at(-1)) }
      });
    }
    if (this.$route.name !== 'resourcePool') {
      this.handleExpandKey([this.menuOptions[0]]);
      this.selectKey = window.atob(this.$route.params.machineId);
      this.expandeds = [this.menuOptions[0].key, window.atob(this.$route.params.machineId)];
      const urlpath = this.$route.path.split('/');
      this.activeTab = urlpath[urlpath.length - 2];
    }
  },
  setup() {
    return {
      typeOptions: extendForm.typeOptions,
      handleLoad: extendForm.handleLoad,
      ...modules
    };
  }
};
</script>
<style></style>
