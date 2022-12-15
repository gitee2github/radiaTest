import axios from '@/axios';
import { unkonwnErrorMsg } from '@/assets/utils/description';
function getRequest(url, data) {
  return new Promise((resolve, reject) => {
    axios
      .get(url, data)
      .then((res) => {
        resolve(res);
      })
      .catch((err) => {
        window.$notification?.error({
          content: err.data.error_msg || unkonwnErrorMsg
        });
        reject(err);
      });
  });
}
function getRequestWithoutCatch(url, data) {
  return new Promise((resolve, reject) => {
    axios
      .get(url, data)
      .then((res) => {
        resolve(res);
      })
      .catch((err) => {
        reject(err);
      });
  });
}
export function getRepo(data) {
  return getRequest('/v1/git-repo', data);
}
export function getSuite(data) {
  return getRequest('/v1/suite', data);
}
export function getPm(data) {
  return getRequest('/v1/accessable-machines', {
    machine_type: 'physical',
    ...data
  });
}
export function getVm(data) {
  return getRequest('/v1/accessable-machines', {
    machine_type: 'kvm',
    ...data
  });
}
export function getChildrenJob(id, data) {
  return getRequest(`/v1/job/${id}/children`, data);
}
export function getJob(data) {
  return getRequest('/v1/job', data);
}
export function getTemplateInfo(id, data) {
  return getRequest(`/v1/template/${id}`, data);
}
export function getIssue(data) {
  return getRequest('/v2/milestone/issues', data);
}
export function getRoundIssue(roundId, data) {
  return getRequest(`/v1/round/${roundId}/issues`, data);
}
export function getIssueType(data) {
  return getRequest('/v2/milestone/issue_types', data);
}
export function getAllOrg(data) {
  return getRequest('/v1/login/org/list', data);
}
export function loginByCode(data) {
  return getRequest('/v1/login', data);
}
export function getGroup(data) {
  return getRequest('/v1/groups', data);
}
export function getMsgGroup(data) {
  return getRequest('/v1/msg/group', data);
}
export function getCaseReview(data) {
  return getRequest('/v1/case/commit/query', data);
}
export function getMachineGroup(data) {
  return getRequest('/v1/machine-group', data);
}
export function getRootCert(data) {
  return new Promise((resolve, reject) => {
    axios
      .get('/v1/ca-cert', data, { responseType: 'arraybuffer' })
      .then((res) => {
        resolve(res);
      })
      .catch((err) => {
        reject(err);
        window.$notification?.error({ content: err.data.error_msg || unkonwnErrorMsg });
      });
  });
}
export function getCommitHistory(caseId, data) {
  return getRequest(`/v1/commit/history/${caseId}`, data);
}
export function getPmachine(data) {
  return getRequest('/v1/pmachine', data);
}
export function getPmachineBmc(pmachineId, data) {
  return getRequest(`/v1/pmachine/${pmachineId}/bmc`, data);
}
export function getPmachineSsh(pmachineId, data) {
  return getRequest(`/v1/pmachine/${pmachineId}/ssh`, data);
}
export function getVmachine(data) {
  return getRequest('/v1/vmachine', data);
}
export function getVmachineSsh(vmachineId, data) {
  return getRequest(`/v1/vmachine/${vmachineId}/ssh`, data);
}
export function getCaseReviewDetails(id, data) {
  return getRequest(`/v1/case/commit/${id}`, data);
}
export function getCaseReviewComment(id, data) {
  return getRequest(`/v1/case/${id}/comment`, data);
}
export function getCaseDetail(id, data) {
  return getRequest(`/v1/case/${id}`, data);
}
export function getCasePrecise(data) {
  return getRequest('/v1/case', data);
}
export function getExtendRole(data) {
  return getRequest('/v1/role/default', data);
}
export function getMilestoneTask(milestoneId, data) {
  return getRequest(`/v1/milestone/${milestoneId}/tasks`, data);
}
export function getMilestone(productId, data) {
  return getRequest(`/v1/milestone/preciseget?product_id=${productId}`, data);
}
export function getAllMilestone(data) {
  return getRequest('v2/milestone', data);
}
export function getProductMessage(productId, data) {
  return getRequest(`/v1/qualityboard?product_id=${productId}`, data);
}
export function getMilestoneRate(milestoneId, data) {
  return getRequest(`/v2/milestone/${milestoneId}/issues-statistics?is_live=False`, data);
}
export function getMachineGroupDetails(id, data) {
  return getRequest(`/v1/machine-group/${id}`, data);
}
export function getCaseCommit(data) {
  return getRequest('/v1/user/case/commit', data);
}
export function getIssueDetails(id, data) {
  return getRequest(`/v2/milestone/issues/${id}`, data);
}
export function getPendingReview(data) {
  return getRequest('/v1/case/commit/status', data);
}
export function getAllRole(data) {
  return getRequest('/v1/role', data);
}
export function getOrgUser(id, data) {
  return getRequest(`/v1/org/${id}/users`, data);
}
export function getOrgGroup(id, data) {
  return getRequest(`/v1/org/${id}/groups`, data);
}
export function getProduct(data) {
  return getRequest('/v1/product', data);
}
export function getCaseNodeTask(id, data) {
  return getRequest(`/v1/case-node/${id}/task`, data);
}
export function getOrgNode(id, data) {
  return getRequest(`/v1/org/${id}/resource`, data);
}

export function getTermNode(id, data) {
  return getRequest(`/v1/group/${id}/resource`, data);
}

export function getGroupRepo(id) {
  return getRequest(`/v1/git-repo/${id}`);
}

export function getAtOverview(id, params) {
  return getRequest(`/v1/qualityboard/${id}/at`, params);
}

export function getQualityDefend(id, params) {
  return getRequest(`/v1/qualityboard/${id}/quality-defend`, params);
}

export function getDailyBuildSingle(id) {
  return getRequest(`/v1/dailybuild/${id}`);
}

export function getDailyBuildBatch(id, params) {
  return getRequest(`/v1/qualityboard/${id}/dailybuild`, params);
}

export function getWeeklybuildData(id, params) {
  return getRequest(`/v1/qualityboard/${id}/weeklybuild-health`, params);
}

export function getWeeklybuildDetail(id) {
  return getRequest(`/v1/weeklybuild/${id}`);
}

export function getFeatureCompletionRates(id) {
  return getRequest(`/v1/qualityboard/${id}/feature-list/summary`);
}

export function getFeatureList(id, params) {
  return getRequest(`/v1/qualityboard/${id}/feature-list`, params);
}

export function getPackageListComparationSummaryAxios(qualityboardId, roundId, params) {
  return getRequestWithoutCatch(`/v1/qualityboard/${qualityboardId}/round/${roundId}/pkg-list`, params);
}

export function getPackageListComparationDetail(qualityboardId, roundPreId, roundCurId, params) {
  return getRequestWithoutCatch(
    `/v1/qualityboard/${qualityboardId}/round/${roundPreId}/with/${roundCurId}/pkg-compare`,
    params
  );
}

export function getCheckListTableRounds(data) {
  return getRequest('/v1/checklist/rounds-count', data);
}

export function getCheckListTableDataAxios(data) {
  return getRequest('/v1/checklist', data);
}

export function getMilestonesByName(data) {
  return getRequest('/v2/gitee-milestone', data);
}

export function getUserAssetRank(params) {
  return getRequest('/v1/user/rank', params);
}

export function getGroupAssetRank(params) {
  return getRequest('/v1/group/rank', params);
}

export function getUserInfo(userId, params) {
  return getRequest(`/v1/users/${userId}`, params);
}

export function getRequireList(params) {
  return getRequest('/v1/requirement', params);
}

export function getRequireItem(id, params) {
  return getRequest(`/v1/requirement/${id}`, params);
}

export function getRequireProgress(id, params) {
  return getRequest(`/v1/requirement/${id}/progress`, params);
}

export function getRequirePackage(id, params) {
  return getRequest(`/v1/requirement/${id}/package`, params);
}

export function downloadAttachment(id, params) {
  return getRequest(`/v1/requirement/${id}/attachment/download`, params);
}

export function getAttachmentList(id, params) {
  return getRequest(`/v1/requirement/${id}/attachment`, params);
}

export function getRequireAttributors(id, params) {
  return getRequest(`/v1/requirement/${id}/attributor`, params);
}

export function getMilestones(data) {
  return getRequest('/v2/milestone', data);
}

export function getRoundIssueRate(roundId) {
  return getRequest(`/v1/round/${roundId}/issue-rate`);
}

export function getHomonymousIsomerismPkgcompare(qualityboardId, roundId, params) {
  return getRequestWithoutCatch(`/v1/qualityboard/${qualityboardId}/round/${roundId}/pkg-compare`, params);
}

export function examplesNodes(id, data) {
  return getRequest(`/v1/org/${id}/resource`, data);
}

export function getCaseNodeResource(id, data) {
  return getRequest(`/v1/case-node/${id}/resource`, data);
}

export function getBaselineTemplates(data) {
  return getRequest('/v1/baseline-template', data);
}

export function getBaselineTemplateItem(id, data) {
  return getRequest(`/v1/baseline-template/${id}`, data);
}

export function getScopedGitRepo(data) {
  return getRequest('/v1/git-repo/scoped', data);
}

export function getFramework(data) {
  return getRequest('/v1/framework', data);
}

export function getSuiteDocuments(suiteId, data) {
  return getRequest(`/v1/suite/${suiteId}/document`, data);
}

export function getBaseNode(baseNodeId, data) {
  return getRequest(`/v1/base-node/${baseNodeId}`, data);
}

export function getCaseSetNodes(_type, id, data) {
  return getRequest(`/v1/${_type}/${id}/caseset`, data);
}

export function getCaseNode(caseNodeId, data) {
  return getRequest(`/v1/case-node/${caseNodeId}`, data);
}

export function getGroupMilestone(groupId, data) {
  return getRequest(`/v1/group/${groupId}/milestone`, data);
}

export function getOrgMilestone(orgId, data) {
  return getRequest(`/v1/org/${orgId}/milestone`, data);
}

export function getCaseNodeRoot(caseNodeId, data) {
  return getRequest(`/v1/case-node/${caseNodeId}/get-root`, data);
}

export function getSuiteItem(suiteId) {
  return getRequest(`/v1/suite/${suiteId}`);
}

export function getManualJob(data) {
  return getRequest('/v1/manual-job', data);
}

export function getManualJobLog(jobId, stepId) {
  return getRequest(`/v1/manual-job/${jobId}/step/${stepId}`);
}
