const m = require("mithril");
const ChartComponent = require("../components/chart");
const DiscardReportModel = require("../models/discard_report");

class DiscardReportView {
  constructor() {
    this.model = new DiscardReportModel();
    this.windows = [
      { value: "5m", label: "Last 5 minutes" },
      { value: "1h", label: "Last 1 hour" },
      { value: "1d", label: "Last 1 day" },
    ];
    this.groupings = [
      { value: "country", label: "Country" },
      { value: "browserFamily", label: "Browser family" },
      { value: "osFamily", label: "OS family" },
      { value: "isMobile", label: "Is mobile" },
      { value: "deviceFamily", label: "Device family" },
      { value: "isBot", label: "Is bot" },
    ];
  }

  oninit() {
    this.model.initialize();
  }

  _formatPercent(value) {
    return `${(value * 100).toFixed(1)}%`;
  }

  _chartOptions() {
    const content = this.model.content || { rows: [] };
    return {
      type: "bar",
      data: {
        labels: content.rows.map(function (row) {
          return row.value;
        }),
        datasets: [
          {
            label: "Discards",
            data: content.rows.map(function (row) {
              return row.count;
            }),
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          colors: {
            enabled: true,
          },
          legend: {
            display: false,
          },
        },
      },
    };
  }

  _renderFilters() {
    return m(".row.g-4", [
      m(
        ".col-sm-12.col-md-6.col-xl-4",
        m(".h-100.bg-light.rounded.p-4", [
          m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Campaign")),
          m(
            "select.form-select",
            {
              "aria-label": "Campaign",
              value: this.model.filter.campaignId || "",
              oninput: function (event) {
                this.model.filter.campaignId = Number(event.target.value);
                this.model.loadReport();
              }.bind(this),
            },
            this.model.campaigns.map(function (campaign) {
              return m("option", { value: campaign.id }, campaign.name);
            }),
          ),
          this.model.campaignError ? m(".text-danger.small.mt-2", this.model.campaignError) : null,
        ]),
      ),
      m(
        ".col-sm-12.col-md-6.col-xl-4",
        m(".h-100.bg-light.rounded.p-4", [
          m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Window")),
          m(
            "select.form-select",
            {
              "aria-label": "Window",
              value: this.model.filter.window,
              oninput: function (event) {
                this.model.filter.window = event.target.value;
                this.model.loadReport();
              }.bind(this),
            },
            this.windows.map(function (window) {
              return m("option", { value: window.value }, window.label);
            }),
          ),
        ]),
      ),
      m(
        ".col-sm-12.col-md-6.col-xl-4",
        m(".h-100.bg-light.rounded.p-4", [
          m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Group By")),
          m(
            "select.form-select",
            {
              "aria-label": "Group By",
              value: this.model.filter.groupBy,
              oninput: function (event) {
                this.model.filter.groupBy = event.target.value;
                this.model.loadReport();
              }.bind(this),
            },
            this.groupings.map(function (grouping) {
              return m("option", { value: grouping.value }, grouping.label);
            }),
          ),
        ]),
      ),
    ]);
  }

  _renderSummary() {
    const content = this.model.content;
    if (!content) {
      return null;
    }

    return m(".row.g-4.mt-1", [
      m(
        ".col-sm-12.col-md-6.col-xl-3",
        m(".bg-light.rounded.d-flex.align-items-center.justify-content-between.p-4", [
          m(".ms-3", [m("p.mb-2", "Discards"), m("h6.mb-0", content.summary.discardCount)]),
        ]),
      ),
      m(
        ".col-sm-12.col-md-6.col-xl-3",
        m(".bg-light.rounded.d-flex.align-items-center.justify-content-between.p-4", [
          m(".ms-3", [m("p.mb-2", "Total events"), m("h6.mb-0", content.summary.totalCount)]),
        ]),
      ),
      m(
        ".col-sm-12.col-md-6.col-xl-3",
        m(".bg-light.rounded.d-flex.align-items-center.justify-content-between.p-4", [
          m(".ms-3", [m("p.mb-2", "Discard rate"), m("h6.mb-0", this._formatPercent(content.summary.rate))]),
        ]),
      ),
      m(
        ".col-sm-12.col-md-6.col-xl-3",
        m(".bg-light.rounded.d-flex.align-items-center.justify-content-between.p-4", [
          m(".ms-3", [m("p.mb-2", "Eligible"), m("h6.mb-0", content.summary.eligible ? "Yes" : "No")]),
        ]),
      ),
    ]);
  }

  _renderChart() {
    const content = this.model.content;
    if (!content) {
      return null;
    }

    return m(
      ".col-sm-12.col-xl-7",
      m(".bg-light.text-center.rounded.p-4.h-100", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Discard distribution")),
        content.rows.length === 0
          ? m(".text-muted.py-5", "No discards in the selected window.")
          : m(ChartComponent, { chartOptions: this._chartOptions() }),
      ]),
    );
  }

  _renderTable() {
    const content = this.model.content;
    if (!content) {
      return null;
    }

    return m(
      ".col-sm-12.col-xl-5",
      m(".bg-light.text-center.rounded.p-4.h-100", [
        m(".d-flex.align-items-center.justify-content-between.mb-4", m("h6.mb-0", "Breakdown rows")),
        content.rows.length === 0
          ? m(".text-muted.py-5", "No grouped rows to display.")
          : m("div.table-responsive", [
              m("table.table.table-striped.mb-0", [
                m("thead", m("tr", [m("th", "Value"), m("th", "Count"), m("th", "Share")])),
                m(
                  "tbody",
                  content.rows.map(
                    function (row) {
                      return m("tr", [
                        m("td", row.value),
                        m("td", row.count),
                        m("td", this._formatPercent(row.share)),
                      ]);
                    }.bind(this),
                  ),
                ),
              ]),
            ]),
      ]),
    );
  }

  view() {
    return m(".container-fluid.pt-4.px-4", [
      this._renderFilters(),
      this.model.isLoading ? m(".bg-light.rounded.p-4.mt-4", "Loading discard report...") : null,
      this.model.error ? m(".alert.alert-danger.mt-4", this.model.error) : null,
      this.model.content ? this._renderSummary() : null,
      this.model.content ? m(".row.g-4.mt-1", [this._renderChart(), this._renderTable()]) : null,
    ]);
  }
}

module.exports = DiscardReportView;
