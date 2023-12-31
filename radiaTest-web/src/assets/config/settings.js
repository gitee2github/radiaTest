const name = 'radiaTest';
const version = '1.0.0';
const license = 'Mulan PSL v2';

const serverPath = 'radiatest.openeuler.org';
const websocketProtocol = 'wss';

const newsSocketPath = `${websocketProtocol}://${serverPath}/message`;

export default {
  name,
  version,
  license,
  serverPath,
  websocketProtocol,
  newsSocketPath,
};
