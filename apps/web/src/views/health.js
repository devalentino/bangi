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

  _historyPanel() {
    return m(".col-sm-12.col-xl-6", [
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
    return m(".container-fluid.pt-4.px-4", [
      this.model.isLoading ? m(".bg-light.rounded.p-4.mb-4", "Loading system health...") : null,
      this.model.error ? m(".alert.alert-danger.mb-4", this.model.error) : null,
      this.model.summary ? m(".row.g-4", [this._usagePanel(), this._historyPanel()]) : null,
    ]);
  }
}

module.exports = HealthView;
