<template>
  <n-card
    :bordered="false"
    size="huge"
    content-style="padding:5px 50px"
    :segmented="{
      content: 'hard',
    }"
    style="height: 100%"
    header-style="
            font-size: 30px;
            height: 80px;
            font-family: 'v-sans';
            padding-top: 40px;
            background-color: rgb(242,242,242);
        "
  >
    <template #header>
      <div class="nav-body">
        <ul class="nav-wrapper">
          <li
            v-for="(item, index) in menu"
            :key="index"
            @click="menuClick(item, index)"
          >
            <a :class="{ active: isTabActive(item.name) }">{{ item.text }}</a>
          </li>
        </ul>
      </div>
    </template>
    <template #default>
      <router-view></router-view>
    </template>
  </n-card>
</template>
<script>
import { modules } from './modules';

import { defineComponent } from 'vue';

export default defineComponent({
  setup() {
    return {
      ...modules,
    };
  }
});


</script>
<style scoped lang="less">
.nav-header {
  display: flex;
  align-items: center;
}

.nav-body {
  position: relative;
  white-space: nowrap;
  z-index: 1;
  display: -ms-flexbox;
  display: -webkit-box;
  display: flex;
  -ms-flex-pack: center;
  -webkit-box-pack: center;
  justify-content: center;

  .nav-wrapper {
    position: relative;
    border: none;
    list-style-type: none;
    padding: 0;

    li {
      list-style: none;
      float: left;
      z-index: 2;
      padding: 0 20px;

      a {
        display: inline-block;
        position: relative;
        margin: 0;
        color: #383838;
        font-size: 15px;
        font-weight: 400;
        cursor: pointer;
        border-bottom: 3px solid #fafafa;

        &.active {
          border-bottom: 3px solid #3da8f5;
        }
      }
    }
  }
}

</style>
