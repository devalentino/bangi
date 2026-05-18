var m = require("mithril");

function severityClass(alerts) {
  if (!alerts) {
    return "text-muted";
  }

  var severity = alerts.highestSeverity();

  if (severity === "error") {
    return "alerts-bell-icon alerts-bell-icon-error";
  }

  if (severity === "warning") {
    return "alerts-bell-icon alerts-bell-icon-warning";
  }

  if (severity === "info") {
    return "alerts-bell-icon alerts-bell-icon-info";
  }

  return "text-muted";
}

function alertIconClass(code) {
  if (code === "core_campaign_discard") {
    return "fa fa-exclamation-triangle";
  }

  if (
      code === "system_health_disk_warning"
      || code === "system_health_disk_critical"
      || code === "system_health_telemetry_stale"
  ) {
    return "fa fa-hdd";
  }

  if (
      code === "system_health_certificate_issuance_failed"
      || code === "system_health_certificate_renewal_warning"
      || code === "system_health_certificate_renewal_error"
      || code === "system_health_certificate_expired"
  ) {
    return "fa fa-lock";
  }

  if (code === "system_health_nginx_validation_failed") {
    return "fa fa-server";
  }

  if (
      code === "facebook_pacs_business_portfolio_access_url_missing"
      || code === "facebook_pacs_business_portfolio_access_url_expiring_soon"
      || code === "facebook_pacs_business_portfolio_access_url_expired"
  ) {
    return "fa fa-laptop";
  }

  return "fa fa-bell";
}

function itemSeverityClass(severity) {
  if (severity === "error") {
    return "alerts-bell-icon-error";
  }

  if (severity === "warning") {
    return "alerts-bell-icon-warning";
  }

  if (severity === "info") {
    return "alerts-bell-icon-info";
  }

  return "text-muted";
}

class AlertsBell {
  view(vnode) {
    var alerts = vnode.attrs.alerts;
    var isDisabled = !alerts || !alerts.hasAlerts();

    return m(".nav-item.dropdown", [
      m(
        "a.nav-link.position-relative",
        {
          href: "#",
          class: isDisabled ? "disabled" : "",
          "data-bs-toggle": isDisabled ? null : "dropdown",
          "aria-disabled": isDisabled ? "true" : null,
          onclick: function (event) {
            if (isDisabled) {
              event.preventDefault();
            }
          },
        },
        m("i", {
          class: `fa fa-bell ${severityClass(alerts)}`,
        }),
      ),
      isDisabled
        ? null
        : m(
          ".dropdown-menu.dropdown-menu-end.bg-light.border-0.rounded-0.rounded-bottom.m-0.p-0.alerts-dropdown",
          alerts.items.map(function (item) {
            return m(".alerts-dropdown-item.border-bottom", [
              m(".d-flex.align-items-start.gap-3", [
                m("i", {
                  class: `${alertIconClass(item.code)} alerts-item-icon ${itemSeverityClass(item.severity)}`,
                }),
                m(".flex-grow-1", [
                  m(".small.mb-0", item.message),
                ]),
              ]),
            ]);
          }),
        ),
    ]);
  }
}

module.exports = AlertsBell;
