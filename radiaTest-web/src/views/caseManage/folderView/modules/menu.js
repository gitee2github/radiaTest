import { h, ref } from 'vue';

import axios from '@/axios.js';
import { storage } from '@/assets/utils/storageUtils';
import {
  Organization20Regular,
  Folder16Regular,
  Delete28Regular,
  Box16Regular,
} from '@vicons/fluent';
import {
  GroupsFilled,
  DriveFileRenameOutlineFilled,
  CreateNewFolderOutlined,
} from '@vicons/material';
import { MdRefresh } from '@vicons/ionicons4';
import { FileImport, DatabaseImport, File } from '@vicons/tabler';
import { Database } from '@vicons/fa';
import { ExportOutlined, EditOutlined } from '@vicons/antd';
import { ArchiveOutline } from '@vicons/ionicons5';
import { changeLoadingStatus } from '@/assets/utils/loading';
import { putModalRef, updateModalRef } from './editRef';
import { getDetail } from '@/views/caseManage/folderView/taskDetails/modules/details.js';
import store from '@/store';
import {
  NButton,
  NFormItem,
  NInput,
  NSpace,
  NIcon,
  NSelect,
  NUpload,
  NUploadDragger,
  NText,
  NP,
} from 'naive-ui';
import router from '@/router';
import { createModalRef, createFormRef, importModalRef } from './createRef';

function renderIcon(icon) {
  return () =>
    h(NIcon, null, {
      default: () => h(icon),
    });
}
const suiteInfo = ref();
const renameAction = {
  label: '重命名',
  key: 'renameBaseline',
  icon: renderIcon(DriveFileRenameOutlineFilled),
};
const editAction = {
  label: '修改',
  key: 'editBaseline',
  icon: renderIcon(EditOutlined),
};
const deleteAction = {
  label: '删除',
  key: 'deleteBaseline',
  icon: renderIcon(Delete28Regular),
};
const createChildrenAction = {
  label: '新建',
  key: 'newParent',
  icon: renderIcon(CreateNewFolderOutlined),
  children: [
    {
      label: '子目录',
      key: 'newDirectory',
    },
    {
      label: '测试套',
      key: 'newSuite',
    },
  ],
};
const iconType = {
  org: Organization20Regular,
  group: GroupsFilled,
  directory: Folder16Regular,
  suite: Box16Regular,
  case: File,
};
const commonAction = [
  { label: '刷新', key: 'refresh', icon: renderIcon(MdRefresh) },
  {
    label: '导出为excel',
    key: 'export',
    disabled: true,
    icon: renderIcon(ExportOutlined),
  },
];

const frameworkList = ref([]);

const menuList = ref();
const expandKeys = ref([]);
function selectGroup() {
  if (router.currentRoute.value.name === 'frameWork') {
    expandKeys.value = [`org-${storage.getValue('orgId')}`];
  }
}
function getOrg() {
  axios.get(`/v1/users/${storage.getValue('gitee_id')}`).then((res) => {
    const { data } = res;
    menuList.value = data.orgs.map((item) => {
      if (item.re_user_org_default) {
        return {
          label: item.org_name,
          key: `org-${item.org_id}`,
          iconColor: 'rgba(0, 47, 167, 1)',
          isLeaf: false,
          type: 'org',
          icon: Organization20Regular,
        };
      }
      selectGroup();
      return '';
    });
  });
}
function getGroup(node) {
  return new Promise((resolve, reject) => {
    const actions = [...commonAction];
    actions.unshift({
      label: '导入用例集',
      key: 'importCaseSet',
      icon: renderIcon(DatabaseImport),
    });
    actions.unshift({
      label: '新建目录',
      key: 'newDirectory',
      icon: renderIcon(CreateNewFolderOutlined),
    });
    axios
      .get(`/v1/org/${node.key.replace('org-', '')}/groups`, {
        page_num: 1,
        page_size: 99999,
      })
      .then((res) => {
        node.children = [];
        for (const item of res.data.items) {
          node.children.push({
            label: item.name,
            key: `users-${item.id}`,
            parent: node,
            isLeaf: false,
            info: {
              group_id: item.id,
            },
            type: 'users',
            iconColor: 'rgba(0, 47, 167, 1)',
            icon: GroupsFilled,
            actions,
          });
        }
        resolve(node.children);
      })
      .catch((err) => {
        reject(err);
      });
  });
}

function getDirectory(node) {
  return new Promise((resolve, reject) => {
    axios
      .get('/v1/baseline', {
        group_id: node.key.replace('users-', ''),
      })
      .then((res) => {
        node.children = [];
        for (const item of res.data) {
          const actions = [...commonAction];
          if (!item.in_set) {
            actions.unshift(renameAction);
          } else {
            actions.unshift({
              label: '导入用例',
              key: 'importCase',
              icon: renderIcon(FileImport),
            });
          }
          actions.unshift(createChildrenAction);
          actions.push(deleteAction);
          node.children.push({
            label: item.title,
            key: `directory-${item.id}`,
            isLeaf: false,
            type: item.type,
            info: item,
            iconColor: 'rgba(0, 47, 167, 1)',
            icon: item.title === '用例集' ? Database : iconType[item.type],
            parent: node,
            actions,
          });
        }
        resolve(node.children);
      })
      .catch((err) => {
        reject(err);
      });
  });
}

function getBaseLine(node) {
  return new Promise((resolve, reject) => {
    axios
      .get(`/v1/baseline/${node.info.id}`)
      .then((res) => {
        node.children = [];
        for (const item of res.data.children) {
          const actions = [...commonAction];
          if (item.type === 'suite' || item.type === 'case') {
            actions.unshift(editAction);
          }
          if (!item.in_set) {
            actions.unshift(renameAction);
          } else if (item.type === 'directory') {
            actions.unshift({
              label: '导入用例',
              key: 'importCase',
              icon: renderIcon(FileImport),
            });
          }
          actions.push(deleteAction);
          if (item.type === 'suite') {
            actions.unshift({
              label: '新建测试用例',
              key: 'newCase',
              icon: renderIcon(CreateNewFolderOutlined),
            });
          } else if (item.type === 'directory') {
            actions.unshift(createChildrenAction);
          }
          node.children.push({
            label: item.title,
            info: item,
            key: `${item.type}-${item.id}`,
            isLeaf: item.type === 'case',
            type: item.type,
            iconColor: 'rgba(0, 47, 167, 1)',
            icon: iconType[item.type],
            actions,
            parent: node,
          });
        }
        resolve(node.children);
      })
      .catch((err) => {
        reject(err);
      });
  });
}
function loadData(node, callback) {
  switch (node.type) {
    case 'org':
      getGroup(node)
        .then(() => {
          callback('success');
        })
        .catch((err) => {
          callback(err);
        });
      break;
    case 'users':
      getDirectory(node)
        .then(() => {
          callback('success');
        })
        .catch((err) => {
          callback(err);
        });
      break;
    default:
      getBaseLine(node)
        .then(() => {
          callback('success');
        })
        .catch((err) => {
          callback(err);
        });
      break;
  }
}
const info = ref('');
const inputInfo = ref('');
const infoRules = {
  trigger: ['input', 'blur', 'change'],
  required: true,
  validator() {
    if (info.value === '') {
      return new Error('请填写信息');
    }
    return true;
  },
};
const inputInfoRules = {
  required: true,
  trigger: ['input', 'blur'],
  validator() {
    if (inputInfo.value === '') {
      return new Error('必填项');
    }
    return true;
  },
};
const files = ref();
function validateUploadInfo() {
  // if (!info.value) {
  //   window.$message?.error('请选择测试框架');
  //   return false;
  // }
  const suffix = files.value[0].name.split('.').pop();
  const vaildSuffix = ['rar', 'zip', 'gz', 'xz', 'bz2', 'tar'];
  if (!vaildSuffix.includes(suffix)) {
    window.$message?.error('上传文件格式不对!');
    return false;
  }
  return true;
}
function dialogAction(confirmFn, node, d, contentType) {
  const confirmBtn = h(
    NButton,
    {
      size: 'large',
      type: 'primary',
      ghost: true,
      onClick: () => {
        if (contentType === 'directory') {
          if (infoRules.validator() === true) {
            confirmFn(node);
            d.destroy();
          }
        } else if (contentType === 'caseSet') {
          if (validateUploadInfo()) {
            confirmFn(node);
            d.destroy();
          }
        } else if (
          inputInfoRules.validator() === true &&
          infoRules.validator() === true
        ) {
          confirmFn(node);
          d.destroy();
        } else {
          window.$message?.error('信息有误，请检查!');
        }
      },
    },
    '确定'
  );
  const cancelBtn = h(
    NButton,
    {
      size: 'large',
      type: 'error',
      ghost: true,
      onClick: () => d.destroy(),
    },
    '取消'
  );
  return h(
    NSpace,
    {
      style: 'width:100%',
    },
    [cancelBtn, confirmBtn]
  );
}

function newDectoryContent() {
  const form = h('div', null, [
    h(
      NFormItem,
      {
        label: '名称:',
        rule: infoRules,
      },
      h(NInput, {
        value: info.value,
        onUpdateValue: (value) => {
          info.value = value;
        },
      })
    ),
  ]);
  return form;
}
const suiteList = ref([]);
function getSuite() {
  axios.get('/v1/suite').then((res) => {
    suiteList.value = res.data.map((item) => {
      return {
        label: item.name,
        value: item.id,
      };
    });
  });
}
function newFormContent(titleTip, selectTip, list) {
  if (suiteList.value.length === 0) {
    getSuite();
  }
  const form = h('div', null, [
    h(
      NFormItem,
      {
        label: titleTip,
        rule: inputInfoRules,
      },
      h(NInput, {
        value: inputInfo.value,
        onUpdateValue: (value) => {
          inputInfo.value = value;
        },
      })
    ),
    h(
      NFormItem,
      {
        label: selectTip,
        rule: infoRules,
      },
      h(NSelect, {
        value: info.value,
        options: list,
        onUpdateValue: (value) => {
          info.value = value;
        },
      })
    ),
  ]);
  return form;
}
const caseList = ref();
let currentCase;
function getCase(id) {
  if (currentCase === id) {
    return '';
  }
  currentCase = id;
  axios
    .get('/v1/case', {
      suite_id: id,
    })
    .then((res) => {
      if (Array.isArray(res)) {
        caseList.value = res.data.map((item) => {
          return {
            label: item.name,
            value: item.id,
          };
        });
      }
    })
    .catch((err) => {
      window.$message?.error(err.data.error_msg || '未知错误');
    });
  return '';
}
const description = h(
  NP,
  {
    depth: 3,
    style: 'margin:8px 0 0 0',
  },
  '仅支持zip,rar,tar,gz,xz,bz2压缩文件上传'
);
{
  /* <n-cascader
v-model:value="value"
placeholder="没啥用的值"
:options="options"
:check-strategy="checkStrategyIsChild ? 'child' : 'all'"
:show-path="showPath"
remote
:on-load="handleLoad"
/> */
}
// function renderSelect(label, list) {
//   return h(
//     NFormItem,
//     {
//       label,
//       rule: infoRules,
//     },
//     h(NCascader, {
//       value: info.value,
//       options: list,
//       remote: true,
//       checkStrategy: 'child',
//       showPath: false,
//       onLoad(options) {
//         return new Promise((resolve, reject) => {
//           axios
//             .get('/v1/git_repo', { framework_id: options.value })
//             .then((res) => {
//               options.children = res.data?.map((item) => ({
//                 label: item.git_url,
//                 value: String(item.id),
//                 isLeaf: true,
//               }));
//               resolve();
//             })
//             .catch((err) => reject(err));
//         });
//       },
//       onUpdateValue: (value) => {
//         info.value = value;
//       },
//     })
//   );
// }
function uploadSet(node) {
  const formData = new FormData();
  formData.append('file', files.value[0]?.file);
  formData.append('group_id', node.info.group_id);
  // formData.append('git_repo_id', info.value);
  changeLoadingStatus(true);
  axios
    .post('/v1/baseline/case_set', formData)
    .then(() => {
      window.$message?.success('用例集已上传,请到后台任务查看进展');
      getDirectory(node);
      changeLoadingStatus(false);
    })
    .catch((err) => {
      window.$message?.error(err.data.error_msg || '未知错误');
      changeLoadingStatus(false);
    });
}
function renderUpload() {
  const tip = h(NText, null, '点击或者拖动文件到该区域来上传');
  const icon = h(
    'div',
    {
      style: 'margin-bottom: 12px;',
    },
    h(
      NIcon,
      {
        size: 48,
        depth: 3,
      },
      h(ArchiveOutline)
    )
  );
  return h(
    NUpload,
    {
      action: '/api/v1/baseline/case_set',
      accept: '.rar,.zip,.tar,.gz,.xz,.bz2',
      withCredentials: true,
      max: 1,
      showRemoveButton: false,
      onUpdateFileList: (file) => {
        files.value = file;
      },
      defaultUpload: false,
    },
    h(NUploadDragger, [icon, tip, description])
  );
}

function uploadContent() {
  return h('div', null, [renderUpload()]);
}
function dialogView(confirmFn, node, contentType = 'directory') {
  window.$dialog?.destroyAll();
  const d = window.$dialog?.info({
    title: node.label,
    showIcon: false,
    content: () => {
      switch (contentType) {
        case 'directory':
          return newDectoryContent();
        case 'suite':
          return newFormContent('名称:', '测试套:', suiteList.value);
        case 'case':
          getCase(node.info.suite_id);
          return newFormContent('名称:', '测试用例:', caseList.value);
        case 'caseSet':
          return uploadContent();
        default:
          return newDectoryContent();
      }
    },
    action: () => {
      if (confirmFn) {
        return dialogAction(confirmFn, node, d, contentType);
      }
      return '';
    },
  });
}
function newDirectory(node) {
  axios
    .post('/v1/baseline', {
      title: info.value,
      type: 'directory',
      group_id: node.info.group_id,
      parent_id: node.info.id,
    })
    .then(() => {
      window.$message.success('创建成功');
      if (node.type === 'directory') {
        getBaseLine(node);
      } else {
        getDirectory(node);
      }
    })
    .catch((err) => {
      window.$message.error(err.data.error_msg || '未知错误');
    });
}
function newSuite(node) {
  axios
    .post('/v1/baseline', {
      title: inputInfo.value,
      type: 'suite',
      group_id: node.info.group_id,
      parent_id: node.info.id,
      suite_id: info.value,
    })
    .then(() => {
      window.$message.success('创建成功');
      getBaseLine(node);
    })
    .catch((err) => {
      window.$message.error(err.data.error_msg || '未知错误');
    });
}
function deleteBaseLine(node) {
  axios
    .delete(`/v1/baseline/${node.info.id}`)
    .then(() => {
      const index = node.parent.children.findIndex(
        (item) => item.info.id === node.info.id
      );
      node.parent.children.splice(index, 1);
      if (
        router.currentRoute.value.name === 'taskDetails' &&
        router.currentRoute.value.params.taskid !== 'development'
      ) {
        getDetail(router.currentRoute.value.params.taskid);
      }
    })
    .catch((err) => {
      window.$message.error(err.data.error_msg || '未知错误');
    });
}
function renameBaseLine(node) {
  axios
    .put(`/v1/baseline/${node.info.id}`, {
      title: info.value,
    })
    .then(() => {
      node.label = info.value;
      info.value = '';
    })
    .catch((err) => {
      window.$message.error(err.data.error_msg || '未知错误');
    });
}
function newCase(node, caseId, title) {
  axios
    .post('/v1/baseline', {
      type: 'case',
      group_id: node.info.group_id,
      parent_id: node.info.id,
      case_id: caseId ? caseId : info.value,
      title: title ? title : inputInfo.value,
    })
    .then(() => {
      window.$message?.success('添加成功');
      getBaseLine(node);
    })
    .catch((err) => {
      window.$message?.error(err.data.error_msg || '未知错误');
    });
}
function initDialogViewData() {
  info.value = '';
  inputInfo.value = '';
}
function refreshNode(node) {
  switch (node.type) {
    case 'users':
      getDirectory(node);
      break;
    default:
      getBaseLine(node);
      break;
  }
}
let inSetnode;
let importInfo;
const actionHandlder = {
  newDirectory: {
    handler(contextmenu) {
      initDialogViewData();
      dialogView(newDirectory, contextmenu);
    },
  },
  newSuite: {
    handler(contextmenu) {
      if (contextmenu.info.in_set) {
        window.$message?.info('该功能开发中....');
      } else {
        initDialogViewData();
        dialogView(newSuite, contextmenu, 'suite');
      }
    },
  },
  deleteBaseline: {
    handler(contextmenu) {
      deleteBaseLine(contextmenu);
    },
  },
  renameBaseline: {
    handler(contextmenu) {
      initDialogViewData();
      dialogView(renameBaseLine, contextmenu);
    },
  },
  newCase: {
    handler(contextmenu) {
      if (contextmenu.info.in_set) {
        createModalRef.value.show();
        inSetnode = contextmenu;
      } else {
        initDialogViewData();
        dialogView(newCase, contextmenu, 'case');
      }
    },
  },
  importCaseSet: {
    handler(contextmenu) {
      initDialogViewData();
      dialogView(uploadSet, contextmenu, 'caseSet');
    },
  },
  importCase: {
    handler(contextmenu) {
      // importForm.model.value.group = contextmenu.info.group_id;
      importInfo = contextmenu;
      importModalRef.value.show();
    },
  },
  refresh: {
    handler(contextmenu) {
      refreshNode(contextmenu);
    },
  },
  editBaseline: {
    handler(contextmenu) {
      const [key] = contextmenu.key.split('-');
      if (key === 'suite') {
        const id = contextmenu.info.suite_id;
        axios.get('/v1/suite', { id }).then((res) => {
          [suiteInfo.value] = res;
          putModalRef.value.show();
        });
      } else if (key === 'case') {
        const id = contextmenu.info.case_id;
        axios.get('/v1/case', { id }).then((res) => {
          store.commit('rowData/set', res.data[0]);
          updateModalRef.value.show();
        });
      }
    },
  },
};
function selectAction({ contextmenu, action }) {
  actionHandlder[action.key].handler(contextmenu);
}
const selectKey = ref();
function menuClick({ key, options }) {
  if (!key.length) {
    return;
  }
  selectKey.value = key;
  const [itemkey, id] = key[0].split('-');
  if (itemkey === 'case') {
    router.push({
      path: `/home/tcm/folderview/taskDetail/${id}`,
    });
  } else if (itemkey === 'users') {
    router.push({
      name: 'frameWork',
      params: {
        groupId: window.btoa(window.encodeURI(options[0].label)),
      },
    });
  } else {
    router.push({
      path: '/home/tcm/folderview/taskDetail/development',
    });
  }
}

function findeItem(array, key, value) {
  return array.find((item) => Number(item.info[key]) === Number(value));
}

function getNode(baselineId) {
  axios.get(`/v1/baseline/${baselineId}`).then((res) => {
    const treePath = [];
    treePath.push(res.data.group_id);
    if (Array.isArray(res.data.source) && res.data.source.length) {
      treePath.push(...res.data.source.reverse());
    }
    let index = 0;
    selectKey.value = `case-${treePath[treePath.length - 1]}`;
    treePath.reduce((pre, current, currentIndex) => {
      return new Promise((resolve) => {
        if (currentIndex === 1) {
          getGroup(menuList.value[0]).then((node) => {
            expandKeys.value = [menuList.value[0].key];
            const group = findeItem(node, 'group_id', treePath[index]);
            getDirectory(group).then((directory) => {
              expandKeys.value.push(group.key);
              index++;
              const baseline = findeItem(directory, 'id', treePath[index]);
              resolve(baseline);
            });
          });
        } else {
          pre.then((node) => {
            getBaseLine(node).then((baselines) => {
              index++;
              const baseline = findeItem(baselines, 'id', treePath[index]);
              expandKeys.value.push(node.key);
              resolve(baseline);
            });
          });
        }
      });
    });
  });
}
function submitCreateCase() {
  createFormRef.value.post().then((res) => {
    if (res.result.data.id) {
      newCase(inSetnode, res.result.data.id, res.form.name);
    }
  });
}
function expandNode(baselineId) {
  let timer = null;
  timer = setInterval(() => {
    if (menuList.value[0].key) {
      clearInterval(timer);
      getNode(baselineId);
    }
  }, 500);
}
function expand(option) {
  expandKeys.value = option;
}
function clearSelectKey() {
  selectKey.value = '';
}
function extendSubmit(value) {
  if (!value.file.length) {
    window.$message?.error('请上传用例文本');
    return;
  }
  const formData = new FormData();
  formData.append('file', value.file[0].file);
  formData.append('baseline_id', importInfo.info.id);
  formData.append('group_id', importInfo.info.group_id);
  formData.append('framework_id', value.data.framework_id);
  axios.post('/v1/case/import', formData).then(() => {
    window.$message?.success('上传成功');
  });
}

export {
  suiteInfo,
  frameworkList,
  selectKey,
  menuList,
  expandKeys,
  loadData,
  selectAction,
  menuClick,
  getOrg,
  expand,
  expandNode,
  newCase,
  submitCreateCase,
  clearSelectKey,
  extendSubmit,
};