const m = require("mithril");
const ChartComponent = require("../components/chart");
const HealthModel = require("../models/health");
const { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");
const i18n = require("../i18n");

function formatBytes(size) {
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  const digits = unitIndex === 0 ? 0 : 2;
  return `${size.toFixed(digits)} ${units[unitIndex]}`;
}

class HealthView {
  constructor() {
    this.model = new HealthModel();
    this.showNginxFiles = false;
  }

  oninit() {
    this.model.load();
  }

  _usageRows() {
    const summary = this.model.summary;

    return [
      [i18n.t("health.filesystem"), summary && summary.filesystem ? summary.filesystem : "-"],
      [i18n.t("health.mountpoint"), summary && summary.mountpoint ? summary.mountpoint : "-"],
      [i18n.t("health.totalSize"), summary ? formatBytes(summary.totalBytes) : "-"],
      [i18n.t("health.usedSize"), summary ? formatBytes(summary.usedBytes) : "-"],
      [i18n.t("health.availableSize"), summary ? formatBytes(summary.availableBytes) : "-"],
      [i18n.t("health.usedPercent"), summary && summary.usedPercent !== null ? `${summary.usedPercent.toFixed(1)}%` : "-"],
      [i18n.t("health.lastReceivedLocal"), summary ? timestamp2LocalTime(summary.lastReceivedAt) : "-"],
      [i18n.t("health.lastReceivedUtc"), summary ? timestamp2UtcTime(summary.lastReceivedAt) : "-"],
    ];
  }

  _historyChartOptions() {
    return {
      type: "line",
      data: {
        labels: this.model.history.map(function (row) {
          return row.date;
        }),
        datasets: [
          {
            label: i18n.t("health.usedPercentDataset"),
            data: this.model.history.map(function (row) {
              return row.usedPercent;
            }),
            fill: false,
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          colors: {
            enabled: true,
          },
        },
        scales: {
          y: {
            min: 0,
            max: 100,
            ticks: {
              callback: function (value) {
                return `${value}%`;
              },
            },
          },
        },
      },
    };
  }

  _nginxRows() {
    const snapshot = this.model.nginxSnapshot;

    return [
      [i18n.t("health.validationStatus"), snapshot ? this._nginxStatus() : "-"],
      [i18n.t("health.validationTimestampLocal"), snapshot ? timestamp2LocalTime(snapshot.validationTimestamp) : "-"],
      [i18n.t("health.validationTimestampUtc"), snapshot ? timestamp2UtcTime(snapshot.validationTimestamp) : "-"],
    ];
  }

  _nginxStatus() {
    const snapshot = this.model.nginxSnapshot;

    if (snapshot.validationStatus === "failed") {
      return [
        m("i.fa.fa-times.text-danger.me-2", { title: i18n.t("status.failed") }),
        "failed",
      ];
    }

    return [
        m("i.fa.fa-check.text-success.me-2", { title: i18n.t("health.success") }),
        i18n.t("health.success"),
    ];
  }

  _nginxFileList(title, items) {
    return m(".mb-3", [
      m("h6.mb-3", title),
      items && items.length
        ? m(
            "ul.mb-0",
            items.map(function (item) {
              return m("li", item);
            }),
          )
        : m(".text-muted", "-"),
    ]);
  }

  _nginxFilesPanel() {
    const snapshot = this.model.nginxSnapshot;

    return m(".mt-3", [
      this._nginxFileList(
        i18n.t("health.availableFiles"),
        snapshot.sitesAvailableFiles,
      ),
      this._nginxFileList(
        i18n.t("health.enabledRefs"),
        snapshot.sitesEnabledRefs,
      ),
    ]);
  }

  _certificateStatusText(diagnostic) {
    if (diagnostic.isARecordSet !== true) {
      return i18n.t("health.dnsNotReady");
    }

    if (!diagnostic.status) {
      return i18n.t("health.noCertificate");
    }

    const labels = {
      pending: i18n.t("status.pending"),
      active: i18n.t("status.active"),
      failed: i18n.t("status.failed"),
      expired: i18n.t("status.expired"),
    };

    return labels[diagnostic.status] || diagnostic.status;
  }

  _certificateStatusBadge(diagnostic) {
    const badgeClasses = {
      pending: "badge bg-info text-dark",
      active: "badge bg-success",
      failed: "badge bg-warning text-dark",
      expired: "badge bg-danger",
    };
    const badgeClass = diagnostic.isARecordSet !== true
      ? "badge bg-info text-dark"
      : badgeClasses[diagnostic.status] || "badge bg-secondary";

    return m(
      "span",
      { class: badgeClass },
      this._certificateStatusText(diagnostic),
    );
  }

  _aRecordIcon(diagnostic) {
    return m("i.text-muted", {
      class: diagnostic.isARecordSet ? "fa fa-check" : "fa fa-times",
      title: diagnostic.isARecordSet ? i18n.t("health.aRecordIsSet") : i18n.t("health.aRecordIsNotSet"),
    });
  }

  _certificateDiagnosticsPanel() {
    return m(".col-sm-12", [
      m(".bg-light.rounded.h-100.p-4", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", i18n.t("health.certificateDiagnostics"))),
        this.model.certificateError ? m(".alert.alert-danger.py-2.mb-4", this.model.certificateError) : null,
        this.model.certificateDiagnostics.length === 0
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-lock.fa-2x.mb-3"),
              m("h5.mb-2", i18n.t("health.noCertificateRisks")),
              m(".text-muted", i18n.t("health.noCertificateRisksHelp")),
            ])
          : m(
              "div.table-responsive",
              m("table.table.table-sm.health-certificate-table.align-middle.mb-0", [
                m("thead", [
                  m("tr", [
                    m("th", { scope: "col" }, i18n.t("domains.domain")),
                    m("th", { scope: "col" }, i18n.t("health.certificateStatus")),
                    m("th", { scope: "col" }, i18n.t("domains.aRecord")),
                    m("th", { scope: "col" }, i18n.t("health.expires")),
                    m("th", { scope: "col" }, i18n.t("health.lastAttempt")),
                    m("th", { scope: "col" }, i18n.t("health.failures")),
                    m("th", { scope: "col" }, i18n.t("health.failure")),
                  ]),
                ]),
                m(
                  "tbody",
                  this.model.certificateDiagnostics.map(
                    function (diagnostic) {
                      return m("tr", [
                        m("td", diagnostic.hostname),
                        m("td", this._certificateStatusBadge(diagnostic)),
                        m("td", this._aRecordIcon(diagnostic)),
                        m("td", timestamp2LocalTime(diagnostic.expiresAt)),
                        m("td", timestamp2LocalTime(diagnostic.lastAttemptedAt)),
                        m("td", diagnostic.failureCount),
                        m("td", diagnostic.failureReason || "-"),
                      ]);
                    }.bind(this),
                  ),
                ),
              ]),
            ),
      ]),
    ]);
  }

  _usagePanel() {
    return m(".col-sm-12.col-xl-6", [
      m(".bg-light.rounded.h-100.p-4", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", i18n.t("health.diskUsage"))),
        this.model.summary && this.model.summary.stale
          ? m(".alert.alert-warning.py-2.mb-4", i18n.t("health.telemetryStale"))
          : null,
        this.model.isNeverReported()
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-hdd.fa-2x.mb-3"),
              m("h5.mb-2", i18n.t("health.neverReported")),
              m(".text-muted", i18n.t("health.noStorageInfo")),
            ])
          : m(
              "div.table-responsive",
              m(
                "table.table.table-sm.mb-0",
                m(
                  "tbody",
                  this._usageRows().map(function (row) {
                    return m("tr", [m("th", { scope: "row" }, row[0]), m("td.text-end", row[1])]);
                  }),
                ),
              ),
            ),
      ]),
    ]);
  }

  _nginxPanel() {
    const snapshot = this.model.nginxSnapshot;

    return m(".col-sm-12.col-xl-6", [
      m(".bg-light.rounded.h-100.p-4", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", i18n.t("health.nginxValidation"))),
        this.model.nginxError ? m(".alert.alert-danger.py-2.mb-4", this.model.nginxError) : null,
        !snapshot
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-server.fa-2x.mb-3"),
              m("h5.mb-2", i18n.t("health.noValidationSnapshot")),
              m(".text-muted", i18n.t("health.noValidationSnapshotHelp")),
            ])
          : [
              m(
                "div.table-responsive",
                m(
                  "table.table.table-sm.mb-0",
                  m(
                    "tbody",
                    this._nginxRows().map(function (row) {
                      return m("tr", [m("th", { scope: "row" }, row[0]), m("td.text-end", row[1])]);
                    }),
                  ),
                ),
              ),
              m(
                "button.btn.btn-link.nav-link mt-3 p-0",
                {
                  type: "button",
                  onclick: function () {
                    this.showNginxFiles = !this.showNginxFiles;
                  }.bind(this),
                },
                [
                  m("i.me-2", {
                    class: this.showNginxFiles
                      ? "fa fa-chevron-down"
                      : "fa fa-chevron-right",
                  }),
                  i18n.t("health.nginxFiles"),
                ],
              ),
              this.showNginxFiles
                ? this._nginxFilesPanel()
                : null,
              snapshot.validationStatus === "failed" && snapshot.validationError
                ? m("pre.bg-white.border.rounded.p-3.mt-3.mb-0", snapshot.validationError)
                : null,
            ],
      ]),
    ]);
  }

  _historyPanel() {
    return m(".col-sm-12", [
      m(".bg-light.rounded.h-100.p-4", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", i18n.t("health.diskHistory"))),
        this.model.isNeverReported()
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-chart-line.fa-2x.mb-3"),
              m("h5.mb-2", i18n.t("health.neverReported")),
              m(".text-muted", i18n.t("health.noDiskHistory")),
            ])
          : m(".health-chart-container", m(ChartComponent, { chartOptions: this._historyChartOptions() })),
      ]),
    ]);
  }

  view() {
    const hasDiskSummary = this.model.summary !== null;
    const hasNginxSnapshot = this.model.nginxSnapshot !== null || this.model.nginxError !== null;
    const hasCertificateDiagnostics =
      this.model.certificateDiagnostics.length > 0 || this.model.certificateError !== null;

    return m(".container-fluid.pt-4.px-4", [
      this.model.isLoading ? m(".bg-light.rounded.p-4.mb-4", i18n.t("health.loading")) : null,
      this.model.error ? m(".alert.alert-danger.mb-4", this.model.error) : null,
      hasDiskSummary
        ? m("div", [
            m(".row.g-4", [this._usagePanel(), this._nginxPanel()]),
            m(".row.g-4.mt-0", [this._certificateDiagnosticsPanel()]),
            m(".row.g-4.mt-0", [this._historyPanel()]),
          ])
        : null,
      !hasDiskSummary && hasNginxSnapshot ? m(".row.g-4", [this._nginxPanel()]) : null,
      !hasDiskSummary && !hasNginxSnapshot && hasCertificateDiagnostics
        ? m(".row.g-4", [this._certificateDiagnosticsPanel()])
        : null,
    ]);
  }
}

module.exports = HealthView;
