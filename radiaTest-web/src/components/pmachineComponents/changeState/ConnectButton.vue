<template>
  <n-tooltip trigger="hover">
    <template #trigger>
      <n-button
        :disabled="disabled"
        v-show="connectShow"
        size="medium"
        type="info"
        @click="() => !disabled && handleConnectClick(data, 'occupy')"
        circle
      >
        <n-icon size="20">
          <connect />
        </n-icon>
      </n-button>
    </template>
    占用
  </n-tooltip>
  <n-tooltip trigger="hover">
    <template #trigger>
      <n-button
        v-show="!connectShow"
        size="medium"
        :disabled="disabled"
        type="info"
        @click="() => !disabled && handleConnectClick(data, 'release')"
        circle
      >
        <n-icon size="20">
          <disconnect />
        </n-icon>
      </n-button>
    </template>
    释放
  </n-tooltip>
</template>

<script>
import { computed, defineComponent } from 'vue';

import {
  PlugDisconnected20Filled as Disconnect,
  Connector20Filled as Connect,
} from '@vicons/fluent';
import {
  handleConnectClick,
} from '@/views/pmachine/modules/changeState/connect.js';

export default defineComponent({
  components: {
    Disconnect,
    Connect,
  },
  props: {
    data: Object,
    disabled: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const connectShow = computed(() => props.data.state === 'idle');
    return {
      connectShow,
      handleConnectClick,
    };
  },
});
</script>

<style scoped></style>
