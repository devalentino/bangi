var m = require("mithril");
require("./styles/app.css");

var api = require("./src/models/api");
var session = require("./src/models/session");
var AuthenticatedPage = require("./src/components/authenticated_page");
var authView = require("./src/views/auth");
var healthView = require("./src/views/health");
var statisticsView = require("./src/views/statistics");
var expensesReportView = require("./src/views/expenses_report");
var discardReportView = require("./src/views/discard_report");
var reportsLeadView = require("./src/views/reports_lead");
var reportsLeadsView = require("./src/views/reports_leads");
var coreCampaignView = require("./src/views/core_campaign");
var coreCampaignsView = require("./src/views/core_campaigns");
var coreFlowView = require("./src/views/core_flow");
var facebookPacsExecutorsView = require("./src/views/facebook_pacs_executors");
var facebookPacsExecutorView = require("./src/views/facebook_pacs_executor");
var facebookPacsBusinessPortfoliosView = require("./src/views/facebook_pacs_business_portfolios");
var facebookPacsBusinessPortfolioView = require("./src/views/facebook_pacs_business_portfolio");
var facebookPacsBusinessPortfolioAccessUrlsView = require(
  "./src/views/facebook_pacs_business_portfolio_access_urls",
);
var facebookPacsBusinessPortfolioAccessUrlView = require(
  "./src/views/facebook_pacs_business_portfolio_access_url",
);
var facebookPacsAdCabinetsView = require("./src/views/facebook_pacs_ad_cabinets");
var facebookPacsAdCabinetView = require("./src/views/facebook_pacs_ad_cabinet");
var facebookPacsCampaignsView = require("./src/views/facebook_pacs_campaigns");
var facebookPacsCampaignView = require("./src/views/facebook_pacs_campaign");
var facebookPacsBusinessPagesView = require("./src/views/facebook_pacs_business_pages");
var facebookPacsBusinessPageView = require("./src/views/facebook_pacs_business_page");

var auth = session.auth;
var alerts = session.alerts;

m.route(document.getElementById("content"), "/statistics", {
  "/sign-in": {
    onmatch: function () {
      if (auth.isAuthenticated) {
        m.route.set("");
      }
    },
    render: function () {
      return m(authView.SignIn, { auth: auth });
    },
  },
  "/health": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: healthView, auth: auth, alerts: alerts });
    },
  },
  "/statistics": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: statisticsView, auth: auth, alerts: alerts });
    },
  },
  "/reports/expenses": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: expensesReportView, auth: auth, alerts: alerts });
    },
  },
  "/reports/discard": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: discardReportView, auth: auth, alerts: alerts });
    },
  },
  "/reports/leads": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: reportsLeadsView, auth: auth, alerts: alerts });
    },
  },
  "/reports/leads/:clickId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: reportsLeadView, auth: auth, alerts: alerts });
    },
  },
  "/core/campaigns": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: coreCampaignsView, auth: auth, alerts: alerts });
    },
  },
  "/core/campaigns/:campaignId/flows/:flowId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: coreFlowView, auth: auth, alerts: alerts });
    },
  },
  "/core/campaigns/:campaignId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: coreCampaignView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/executors": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsExecutorsView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/executors/:executorId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsExecutorView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/business-portfolios": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsBusinessPortfoliosView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/business-portfolios/:businessPortfolioId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsBusinessPortfolioView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/business-portfolios/:businessPortfolioId/access-urls": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsBusinessPortfolioAccessUrlsView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/business-portfolios/:businessPortfolioId/access-urls/new": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsBusinessPortfolioAccessUrlView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/ad-cabinets": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsAdCabinetsView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/ad-cabinets/:adCabinetId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsAdCabinetView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/campaigns": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsCampaignsView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/campaigns/:campaignId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsCampaignView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/business-pages": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsBusinessPagesView, auth: auth, alerts: alerts });
    },
  },
  "/facebook/pacs/business-pages/:businessPageId": {
    onmatch: function () {
      if (!auth.isAuthenticated) {
        m.route.set("/sign-in");
      }
    },
    render: function () {
      return m(AuthenticatedPage, { page: facebookPacsBusinessPageView, auth: auth, alerts: alerts });
    },
  },
});
