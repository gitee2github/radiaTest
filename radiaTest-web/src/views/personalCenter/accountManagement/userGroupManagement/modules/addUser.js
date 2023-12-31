import { ref, reactive, computed } from 'vue';

import axios from '@/axios';
import { storage } from '@/assets/utils/storageUtils';
import { changeLoadingStatus } from '@/assets/utils/loading';
import { groupInfo, showAddUser } from './groupDrawer';

let addUserInfo = reactive({
  name: '',
  value: ''
});
const usersList = ref([]);
function deleteItems (index) {
  usersList.value.splice(index, 1);
}
function searchUser () {
  changeLoadingStatus(true);
  axios.get(`/v1/org/${storage.getValue('loginOrgId')}/users`, {
    page_size: 9999,
    page_num: 1,
    name: addUserInfo.name,
    group_id: groupInfo.id,
  }).then(res => {
    changeLoadingStatus(false);
    let result = [];
    let obj = {};
    if (res.data?.items) {
      usersList.value.push(...res.data.items);
      for (let i of usersList.value) {
        if (!obj[i.gitee_id]) {
          result.push(i);
          obj[i.gitee_id] = true;
        }
      }
      usersList.value = result;
    }
  }).catch((err) => {
    window.$message?.error(err.data.error_msg||'未知错误');
    changeLoadingStatus(false);
  });
}
function initAddInfo () {
  usersList.value = [];
  addUserInfo.name = '';
  addUserInfo.value = '';
}
function cancelAdd () {
  showAddUser.value = !showAddUser.value;
  initAddInfo();
}
function handlePositiveClick () {
  if (usersList.value.length) {
    changeLoadingStatus(true);
    const giteeIds = usersList.value.map(item => {
      return item.gitee_id;
    });
    axios.post(`/v1/groups/${groupInfo.id}/users`, {
      gitee_ids: giteeIds
    }).then(res => {
      changeLoadingStatus(false);
      if (res.error_code === '2000') {
        window.$message?.success('已向用户发送信息!');
      }
      cancelAdd();
    }).catch((err) => {
      window.$message?.error(err.data.error_msg||'未知错误');
      changeLoadingStatus(false);
    });
  } else {
    window.$message.error('不能提交空数据!');
  }
  return false;
}
const options = computed(() => {
  return usersList.value.map((info) => {
    return {
      label: info.gitee_name,
      key: info.gitee_id,
      value: info.gitee_id,
    };
  });
});

export {
  options,
  usersList,
  addUserInfo,
  searchUser,
  deleteItems,
  cancelAdd,
  handlePositiveClick,
};
