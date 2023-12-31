<template>
  <n-data-table
    remote
    ref="table"
    size="large"
    :bordered="false"
    :columns="columns"
    :data="data"
    :loading="loading"
    :row-class-name="(row) => row.state"
    :row-key="(row) => row.id"
    @update:expanded-row-keys="handleExpand"
    @update:checked-row-keys="(keys) => handleCheck(keys, store)"
    @update:sorter="handleSorterChange"
    :scroll-x="1600"
    :pagination="pagination"
    @update:page="handlePageChange"
    @update:page-size="handlePageSizeChange"
  />
</template>

<script>
import { ref, defineComponent } from 'vue';
import { useStore } from 'vuex';
import { Socket } from '@/socket';
import { getPmachine } from '@/api/get';
import settings from '@/assets/config/settings.js';
import pmachineTable from '@/views/pmachine/modules/pmachineTable.js';
import { createColumns } from '@/views/pmachine/modules/pmachineTableColumns.js';
import pmachineFilter from '@/views/pmachine/modules/pmachineFilter';

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
      getPmachine({
        machine_group_id: window.atob(this.$route.params.machineId),
        page_num: this.pagination.page,
        page_size: this.pagination.pageSize,
        ...this.pmachineFilter
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
    pmachineFilter: {
      handler() {
        this.getData();
      },
      deep: true
    }
  },
  mounted() {
    const pmachineSocket = new Socket(`${settings.websocketProtocol}://${settings.serverPath}/pmachine`);
    pmachineSocket.connect();
    pmachineSocket.listen('update', () => {
      this.getData();
    });
    this.getData();
  },
  data() {
    return {
      pagination: {
        page: 1,
        pageCount: 1,
        pageSize: 20,
        showSizePicker: true,
        pageSizes: [5, 10, 20, 50, 100]
      },
    };
  },
  setup(props, context) {
    const store = useStore();

    const updateHandler = (row) => {
      store.commit('rowData/set', JSON.parse(JSON.stringify(row)));
      context.emit('update', row);
    };

    const columns = ref(createColumns(updateHandler));

    return {
      store,
      columns,
      ...pmachineTable,
      pmachineFilter: pmachineFilter.filterValue,
    };
  },
});
</script>

<style>
.state {
  transition: all 0.4s linear;
}
.idle .state {
  background-color: rgb(3, 143, 3) !important;
  color: white !important;
  text-align: center !important;
  font-weight: 700 !important;
}
.occupied .state {
  background-color: rgb(146, 9, 9) !important;
  color: white !important;
  text-align: center !important;
  font-weight: 700 !important;
}
.cols.mac {
  width: 11.5%;
}
.cols.frame {
  width: 6.7%;
}
.cols.state {
  width: 9%;
}
.cols.ip {
  width: 10%;
}
.cols.bmcip {
  width: 10%;
}
.cols.occupier {
  width: 9%;
}
.cols.des {
  width: 9%;
}
.cols.endtime {
  width: 18%;
}
.operation {
  justify-content: center !important;
}
</style>
