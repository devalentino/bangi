const m = require("mithril");
const ChartComponent = require("../components/chart");
const HealthModel = require("../models/health");
const { timestamp2LocalTime, timestamp2UtcTime } = require("../utils/date");

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
      ["Filesystem", summary && summary.filesystem ? summary.filesystem : "-"],
      ["Mountpoint", summary && summary.mountpoint ? summary.mountpoint : "-"],
      ["Total size", summary ? formatBytes(summary.totalBytes) : "-"],
      ["Used size", summary ? formatBytes(summary.usedBytes) : "-"],
      ["Available size", summary ? formatBytes(summary.availableBytes) : "-"],
      ["Used percent", summary && summary.usedPercent !== null ? `${summary.usedPercent.toFixed(1)}%` : "-"],
      ["Last received (local)", summary ? timestamp2LocalTime(summary.lastReceivedAt) : "-"],
      ["Last received (UTC)", summary ? timestamp2UtcTime(summary.lastReceivedAt) : "-"],
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
            label: "Used percent",
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
      ["Validation status", snapshot ? this._nginxStatus() : "-"],
      ["Validation timestamp (local)", snapshot ? timestamp2LocalTime(snapshot.validationTimestamp) : "-"],
      ["Validation timestamp (UTC)", snapshot ? timestamp2UtcTime(snapshot.validationTimestamp) : "-"],
    ];
  }

  _nginxStatus() {
    const snapshot = this.model.nginxSnapshot;

    if (snapshot.validationStatus === "failed") {
      return [
        m("i.fa.fa-times.text-danger.me-2", { title: "Failed" }),
        "failed",
      ];
    }

    return [
      m("i.fa.fa-check.text-success.me-2", { title: "Success" }),
      "success",
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
        "Available files",
        snapshot.sitesAvailableFiles,
      ),
      this._nginxFileList(
        "Enabled refs",
        snapshot.sitesEnabledRefs,
      ),
    ]);
  }

  _certificateStatusText(diagnostic) {
    if (diagnostic.isARecordSet !== true) {
      return "DNS not ready";
    }

    if (!diagnostic.status) {
      return "No certificate";
    }

    const labels = {
      pending: "Pending",
      active: "Active",
      failed: "Failed",
      expired: "Expired",
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
      title: diagnostic.isARecordSet ? "A record is set" : "A record is not set",
    });
  }

  _certificateDiagnosticsPanel() {
    return m(".col-sm-12", [
      m(".bg-light.rounded.h-100.p-4", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Certificate Diagnostics")),
        this.model.certificateError ? m(".alert.alert-danger.py-2.mb-4", this.model.certificateError) : null,
        this.model.certificateDiagnostics.length === 0
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-lock.fa-2x.mb-3"),
              m("h5.mb-2", "No Certificate Risks"),
              m(".text-muted", "Enabled domains do not currently have certificate diagnostics to surface."),
            ])
          : m(
              "div.table-responsive",
              m("table.table.table-sm.health-certificate-table.align-middle.mb-0", [
                m("thead", [
                  m("tr", [
                    m("th", { scope: "col" }, "Domain"),
                    m("th", { scope: "col" }, "Certificate status"),
                    m("th", { scope: "col" }, "A record"),
                    m("th", { scope: "col" }, "Expires"),
                    m("th", { scope: "col" }, "Last attempt"),
                    m("th", { scope: "col" }, "Failures"),
                    m("th", { scope: "col" }, "Failure"),
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
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Disk Usage")),
        this.model.summary && this.model.summary.stale
          ? m(".alert.alert-warning.py-2.mb-4", "Telemetry is stale. The latest successful report is older than the expected reporting window.")
          : null,
        this.model.isNeverReported()
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-hdd.fa-2x.mb-3"),
              m("h5.mb-2", "Never Reported"),
              m(".text-muted", "No storage usage info exists yet. The chart and summary will populate after the first successful telemetry push."),
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
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Nginx Validation")),
        this.model.nginxError ? m(".alert.alert-danger.py-2.mb-4", this.model.nginxError) : null,
        !snapshot
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-server.fa-2x.mb-3"),
              m("h5.mb-2", "No Validation Snapshot"),
              m(".text-muted", "No published Nginx validation snapshot is available yet."),
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
                  "Nginx files",
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
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "30-Day Disk History")),
        this.model.isNeverReported()
          ? m(".health-empty-state.py-5.text-center", [
              m("i.fa.fa-chart-line.fa-2x.mb-3"),
              m("h5.mb-2", "Never Reported"),
              m(".text-muted", "No 30-day storage history is available."),
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
      this.model.isLoading ? m(".bg-light.rounded.p-4.mb-4", "Loading system health...") : null,
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
