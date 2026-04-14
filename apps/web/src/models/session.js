const AuthModel = require("./auth");
const AlertsModel = require("./alerts");

const auth = new AuthModel();
const alerts = new AlertsModel(auth);

auth.onAuthenticated = function () {
  alerts.startPolling();
};

auth.onSignedOut = function () {
  alerts.stopPolling();
};

if (auth.isAuthenticated) {
  alerts.startPolling();
}

module.exports = { auth, alerts };
