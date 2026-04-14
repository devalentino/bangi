const m = require("mithril");
const session = require("./session");

const auth = session.auth;

function request(options) {
  if (!options || typeof options !== "object") {
    return m.request(options);
  }

  const headers = Object.assign({}, options.headers);
  if (auth.token && !headers.Authorization) {
    headers.Authorization = `Basic ${auth.token}`;
  }

  return m.request(Object.assign({}, options, { headers: headers }));
}

module.exports = { request };
