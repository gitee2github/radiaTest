<template>
  <n-data-table
    size="large"
    :bordered="false"
    :columns="columns"
    :data="data"
    :loading="loading"
    :row-key="(row) => row.id"
    @update:expanded-row-keys="handleExpand"
    @update:checked-row-keys="(rowKey) => handleCheck(rowKey)"
    @update:sorter="handleSorterChange"
    :scroll-x="1600"
    :pagination="pagination"
    @update:page="handlePageChange"
    @update:page-size="handlePageSizeChange"
    remote
  />
</template>

<script>
import { ref, defineComponent } from 'vue';
import { useStore } from 'vuex';
import { Socket } from '@/socket';
import settings from '@/assets/config/settings.js';
import { get, selection } from '@/assets/CRUD/read';
import { createColumns } from '@/views/vmachine/modules/vmachineTableColumns.js';
import vmachineTable from '@/views/vmachine/modules/vmachineTable.js';
import { getVmachine } from '@/api/get';
import filterValue from '@/views/vmachine/modules/vmachineFilter';
import { workspace } from '@/assets/config/menu.js';

export default defineComponent({
  methods: {
    handlePageChange(page) {
      this.pagination.page = page;
      this.getData();
    },
    handlePageSizeChange(pageSize) {
      this.pagination.page = 1;
      this.pagination.pageSize = pageSize;
      this.getData();
    },
    getData() {
      this.loading = true;
      getVmachine({
        ...this.filterValue,
        machine_group_id: window.atob(this.$route.params.machineId),
        page_num: this.pagination.page,
        page_size: this.pagination.pageSize,
      }).then(res => {
        this.loading = false;
        this.pagination.pageCount = res.data?.pages || 1;
        this.totalData = res.data?.items || [];
      }).catch(() => {
        this.loading = false;
      });
    }
  },
  watch: {
    filterValue: {
      handler() {
        this.getData();
      },
      deep: true
    }
  },
  mounted() {
    this.vmachineSocket = new Socket(`${settings.websocketProtocol}://${settings.serverPath}/vmachine`);
    this.vmachineSocket.connect();
    this.vmachineSocket.listen('update', () => {
      this.getData();
    });
    this.getData();
  },
  onUnmounted() {
    this.vmachineSocket.disconnect();
  },
  setup() {
    const store = useStore();
    const columns = ref(createColumns());

    return {
      store,
      filterValue: filterValue.filterValue,
      vmachineSocket: null,
      columns,
      pagination: ref({
        page: 1,
        pageCount: 1,
        pageSize: 50,
        showSizePicker: true,
        pageSizes: [5, 10, 20, 50, 100]
      }),
      ...vmachineTable,
      showSelection: () => selection.show(columns),
      offSelection: () => selection.off(columns),
      refreshData: () =>
        get.refresh(
          `/v1/ws/${workspace.value}/machine`,
          vmachineTable.totalData,
          vmachineTable.loading
        ),
      handleSorterChange: (sorter) =>
        vmachineTable.sorterChange(sorter, columns),
    };
  },
});
</script>

<style>
/* .end-time {
  width: 10%;
}
.vm-name {
  width: 18%;
}
.cols.vmachine-operation {
  width: 10%;
} */
</style>
