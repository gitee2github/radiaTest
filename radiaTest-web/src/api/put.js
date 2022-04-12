import { modifySuccessMsg, unkonwnErrorMsg } from '@/assets/utils/description';
import axios from '@/axios';
function putRequest (url, data) {
  return new Promise((resolve, reject) => {
    axios
      .put(url, data)
      .then((res) => {
        window.$message?.success(modifySuccessMsg);
        resolve(res);
      })
      .catch((err) => {
        window.$message?.error(err.data.error_msg || unkonwnErrorMsg);
        reject(err);
      });
  });
}
export function modifyRepo (id, data) {
  return putRequest(`/v1/git_repo/${id}`, data);
}
export function modifyDelayTime (id, data) {
  return putRequest(`/v1/vmachine/${id}/delay`, data);
}
export function modifyCommitStatus (id, data) {
  return putRequest(`/v1/case/commit/${id}`, data);
}
export function modifyCommitStatusBatch (data) {
  return putRequest('/v1/case/commit/status', data);
}
export function modifyCommitInfo (id,data) {
  return putRequest(`/v1/case/commit/${id}`, data);
}
export function modifyMachineGroup(id,data){
  return putRequest(`/v1/machine_group/${id}`,data);
}
