import { h, ref } from 'vue';
import { NAvatar, NIcon, NButton, NSpace } from 'naive-ui';
import claAndEnterprise from '@/components/orgManagement/claAndEnterprise.vue';
import { Construct } from '@vicons/ionicons5';
import { renderTooltip } from '@/assets/render/tooltip';
import { Delete24Regular as Delete } from '@vicons/fluent';
import { registerModel, showRegisterOrgWindow, isCreate, fileList } from './registerOrg';
import { organizationInfo } from '@/api/put';
import textDialog from '@/assets/utils/dialog';

import axios from '@/axios';

const orgs = ref([]);
function getData() {
  axios.get('/v1/admin/org').then((res) => {
    orgs.value = res.data;
  });
}

function cloneRegisterModel(row){
  for(const key in row.cla_verify_params){
    registerModel.urlParams.push({key, 'value': row.cla_verify_params[key]});
  }
  for(const key in row.cla_verify_body){
    registerModel.bodyParams.push({key, 'value': row.cla_verify_params[key]});
  }
  const cloneData = JSON.parse(JSON.stringify(row));
  Object.keys(cloneData).forEach((key) => {
    if (!cloneData[key]) {
      cloneData[key] = undefined;
    }
  });

  registerModel.name = cloneData.organization_name;
  registerModel.claVerifyUrl = cloneData.cla_verify_url;
  registerModel.claSignUrl = cloneData.cla_sign_url;
  registerModel.claRequestMethod = cloneData.cla_request_type;
  registerModel.claPassFlag =  cloneData.cla_pass_flag;
  registerModel.enterpriseId = cloneData.enterprise_id;
  registerModel.enterpreiseJoinUrl = cloneData.enterpreise_join_url;
  registerModel.oauthClientId = cloneData.oauth_client_id;
  registerModel.oauthClientSecret = cloneData.oauth_client_secret;
  registerModel.oauthClientScope = cloneData.oauth_scope?.split(',');
  registerModel.description = cloneData.organization_description;
  registerModel.orgId = cloneData.organization_id;
  registerModel.organizationSvatar = cloneData.organization_avatar;
  fileList.value = [];
  if(row.organization_avatar){
    fileList.value.push({id: 'c',status: 'finished',url: row.organization_avatar});
  }
}

function handleDeleteOrg(row) {
  textDialog('warning', '删除组织', '您确定要删除此组织吗？', () => {
    let deleteFormData = new FormData();
    deleteFormData.append('is_delete', true);
    organizationInfo(row.organization_id, deleteFormData)
      .finally(() => {
        getData();
      });
  });
}

const orgColumns = [
  {
    type: 'expand',
    expandable: (rowData) => rowData.organization_name,
    renderExpand: (rowData) => {
      return h(claAndEnterprise, { info: rowData });
    },
  },
  {
    title: '',
    key: 'organization_avatar',
    align: 'center',
    render(row) {
      return h(NAvatar, {
        size: 'small',
        src: row.organization_avatar,
        style: { background: 'rgba(0,0,0,0)' },
      });
    },
  },
  {
    title: '组织名称',
    key: 'organization_name',
    align: 'center',
  },
  {
    title: '描述',
    key: 'organization_description',
    align: 'center',
  },
  {
    title: '操作',
    key: 'action',
    align: 'center',
    render: (row) => {
      return h(
        NSpace,
        {
          justify: 'center',
          align: 'center',
        },
        [
          renderTooltip(
            h(
              NButton,
              {
                size: 'medium',
                type: 'warning',
                circle: true,
                onClick: () => {
                  isCreate.value = false;
                  showRegisterOrgWindow.value = true;
                  cloneRegisterModel(row);
                }
              },
              h(NIcon, { size: '20' }, h(Construct))
            ),
            '修改'
          ),
          renderTooltip(
            h(
              NButton,
              {
                size: 'medium',
                type: 'error',
                circle: true,
                onClick: () => {
                  handleDeleteOrg(row);
                }
              },
              h(NIcon, { size: '20' }, h(Delete))
            ),
            '删除'
          ),
        ]
      );
    },
  },
];
const pagination = {
  pagesize: 7,
};

export { orgs, pagination, orgColumns, getData };
