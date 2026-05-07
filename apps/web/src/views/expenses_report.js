const m = require("mithril");
const { setDefaultDateRange } = require("../utils/date");
const tabulatorModule = require("tabulator-tables");
const AutocompleteModule = require("@trevoreyre/autocomplete-js");
const Tabulator =
  tabulatorModule.TabulatorFull || tabulatorModule.default || tabulatorModule;
const Autocomplete = AutocompleteModule.default || AutocompleteModule;
const ExpensesReportModel = require("../models/expenses_report");

function normalizeMatrixValue(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  if (typeof value === "number") {
    return value;
  }

  let numeric = Number(value);
  if (!Number.isNaN(numeric) && value !== true && value !== false) {
    return numeric;
  }

  return value;
}

function excelColumnTitle(index) {
  let title = "";
  let num = index + 1;

  while (num > 0) {
    let remainder = (num - 1) % 26;
    title = String.fromCharCode(65 + remainder) + title;
    num = Math.floor((num - 1) / 26);
  }

  return title;
}

const ExpensesReportTable = {
  oncreate(vnode) {
    const state = vnode.state;
    const table = new Tabulator(vnode.dom, {
      layout: "fitColumns",
      data: vnode.attrs.rows,
      columns: vnode.attrs.columns,
      columnDefaults: {
        headerSort: false,
        widthGrow: 1,
      },
      placeholder: "Expenses report",
    });

    vnode.state.table = table;
    vnode.state.isSyncing = false;

    table.on("cellEdited", function () {
      if (state.isSyncing) {
        return;
      }

      vnode.attrs.onChange(table, state);
      vnode.attrs.onValidate();

      m.redraw();
    });

    if (vnode.attrs.onReady) {
      vnode.attrs.onReady(table);
    }
  },
  onremove(vnode) {
    if (vnode.state.table) {
      vnode.state.table.destroy();
    }
  },
  view() {
    return m("div");
  },
};

class ExpensesReportView {
  constructor() {
    this.model = new ExpensesReportModel();
    this.table = null;
    this.distributionParameterAutocomplete = null;
    this.distributionParameterAutocompleteRoot = null;
    this.validationErrors = [];
  }

  oninit() {
    setDefaultDateRange(this.model.filter, "periodStart", "periodEnd");

    this.model.loadCampaigns().then(
      function () {
        if (this.model.campaigns.length > 0) {
          this.model.filter.campaignId = Number(this.model.campaigns[0].id);
          this.model.loadDistributionParameters(this.model.filter.campaignId);
          this.model.loadCampaignDetails(this.model.filter.campaignId);
          this._fetchReport();
        }
      }.bind(this),
    );
  }

  onremove() {
    if (
      this.distributionParameterAutocomplete &&
      this.distributionParameterAutocomplete.destroy
    ) {
      this.distributionParameterAutocomplete.destroy();
    }
  }

  initDistributionParameterAutocomplete(root) {
    if (this.distributionParameterAutocomplete) {
      return;
    }

    this.distributionParameterAutocompleteRoot = root;
    this.distributionParameterAutocomplete = new Autocomplete(root, {
      search: function (input) {
        if (this.model.distributionParameterLocked) {
          return Promise.resolve([]);
        }

        const query = (input || "").toLowerCase();

        return Promise.resolve(
          this.model.distributionParameters.filter(function (item) {
            const value = (item.parameter || "").toLowerCase();
            return value.includes(query);
          }),
        );
      }.bind(this),
      getResultValue: function (result) {
        return result.parameter;
      },
      renderResult: function (result, props) {
        return `<li ${props}>
          <div class="d-flex justify-content-between">
            <span>${result.parameter}</span>
          </div>
        </li>`;
      },
      onSubmit: function (result) {
        if (this.model.distributionParameterLocked) {
          return;
        }

        this.model.distributionParameter = result.parameter;
        this.model
          .loadDistributionParameterValues(
            this.model.filter.campaignId,
            result.parameter,
          )
          .then(
            function () {
              this._refreshTableAppearance();
            }.bind(this),
          );
        this.model.saveError = null;
        this.model.saveSuccess = null;
      }.bind(this),
      autoSelect: true,
      submitOnEnter: true,
    });
  }

  _buildTableFromMatrix() {
    if (!this.model.matrix || this.model.matrix.length === 0) {
      return { columns: [], rows: [] };
    }

    const columnCount = this.model.matrix[0].length;
    const columns = [
      {
        title: excelColumnTitle(0),
        field: "date",
        hozAlign: "left",
        editor: "input",
        frozen: true,
      },
    ];

    for (let i = 1; i < columnCount; i += 1) {
      columns.push({
        title: excelColumnTitle(i),
        field: `c${i}`,
        editor: "input",
        hozAlign: "right",
      });
    }

    const rows = this.model.matrix.map(function (row) {
      const record = { date: row[0] || "" };

      for (let i = 1; i < columnCount; i += 1) {
        record[`c${i}`] = row[i];
      }

      return record;
    });

    return { columns: columns, rows: rows };
  }

  _tableToMatrix(table) {
    const columnCount = table.getColumns().length;
    const data = table.getData();

    return data.map(function (row, rowIndex) {
      const values = new Array(columnCount).fill(null);
      values[0] = row.date || null;
      for (let i = 1; i < columnCount; i += 1) {
        if (rowIndex === 0) {
          values[i] = row[`c${i}`];
        } else {
          values[i] = normalizeMatrixValue(row[`c${i}`]);
        }
      }
      return values;
    });
  }

  _resetToOriginal() {
    this.model.resetToOriginal();
    this.validationErrors = [];
    this._refreshTableAppearance();
  }

  _refreshTableAppearance() {
    if (!this.table) {
      return Promise.resolve();
    }

    const tableState = this._buildTableFromMatrix();
    this.table.setColumns(tableState.columns || []);
    return this.table.setData(tableState.rows || []).then(
      function () {
        this._validateTable();
      }.bind(this),
    );
  }

  _fetchReport() {
    return this.model.loadExpensesReport().then(
      function () {
        return this._refreshTableAppearance();
      }.bind(this),
    );
  }

  _isValidDateString(value) {
    if (typeof value !== "string") {
      return false;
    }

    const trimmed = value.trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      return false;
    }

    const parsed = Date.parse(trimmed);
    if (Number.isNaN(parsed)) {
      return false;
    }

    const check = new Date(parsed).toISOString().slice(0, 10);
    return check === trimmed;
  }

  _clearValidationMarkers() {
    if (!this.table) {
      return;
    }

    this.table.getRows().forEach(function (row) {
      row.getCells().forEach(function (cell) {
        const element = cell.getElement();
        element.classList.remove("is-invalid");
        element.removeAttribute("title");
        element.removeAttribute("data-validation-error");
      });
    });
  }

  _markInvalid(cell, message) {
    const element = cell.getElement();
    element.classList.add("is-invalid");
    if (message) {
      element.setAttribute("title", message);
      element.setAttribute("data-validation-error", message);
    }
  }

  _validateTable() {
    if (!this.table) {
      this.validationErrors = [];
      return;
    }

    this._clearValidationMarkers();

    const errors = [];
    const rows = this.table.getRows();
    const headerRow = rows[0];
    const columnCount = this.model.matrix[0].length;

    // Ensure column with value has distribution key
    if (headerRow) {
      for (let i = 1; i < columnCount; i += 1) {
        const field = `c${i}`;
        const hasValue = rows.slice(1).some(function (row) {
          const cell = row.getCell(field);
          const value = cell.getValue();
          return value !== null && value !== undefined && value !== "";
        });

        if (hasValue) {
          const headerCell = headerRow.getCell(field);
          const headerValue = headerCell.getValue();

          const headerValid =
            typeof headerValue === "string" && headerValue.trim() !== "";

          if (!headerValid) {
            const message = `Missing distribution key for column ${excelColumnTitle(i)}.`;
            this._markInvalid(headerCell, message);
            errors.push(message);
          }
        }
      }
    }

    // Ensure rest of table is valid
    rows.slice(1).forEach(
      function (row, rowIndex) {
        const dateCell = row.getCell("date");
        const dateValue = dateCell.getValue();
        let hasValues = false;

        // ensure every row with value has date
        for (let i = 1; i < columnCount; i += 1) {
          const cell = row.getCell(`c${i}`);
          const value = cell.getValue();
          if (value !== null && value !== undefined && value !== "") {
            hasValues = true;
            break;
          }
        }

        if (hasValues) {
          if (dateValue === null || dateValue === undefined || dateValue === "") {
            const message = `Missing date in row ${rowIndex + 2}.`;
            this._markInvalid(dateCell, message);
            errors.push(message);
          } else if (!this._isValidDateString(String(dateValue))) {
            const message = `Invalid date in row ${rowIndex + 2}.`;
            this._markInvalid(dateCell, message);
            errors.push(message);
          }
        } else if (
          dateValue !== null &&
          dateValue !== undefined &&
          dateValue !== ""
        ) {
          if (!this._isValidDateString(String(dateValue))) {
            const message = `Invalid date in row ${rowIndex + 2}.`;
            this._markInvalid(dateCell, message);
            errors.push(message);
          }
        }

        // ensure distribution values are valid
        for (let i = 1; i < columnCount; i += 1) {
          const cell = row.getCell(`c${i}`);

          const value = cell.getValue();
          const headerValue = headerRow.getCell(`c${i}`).getValue();
          if (
            (value === null || value === undefined || value === "")
            && (headerValue !== null && headerValue !== undefined && headerValue !== "")
            && (dateValue !== null && dateValue !== undefined && dateValue !== "")
          ) {
            const message = `Value should not be empty in row ${rowIndex + 2}.`;
            this._markInvalid(cell, message);
            errors.push(message);
            continue;
          }

          const numeric = Number(value);
          if (Number.isNaN(numeric) || numeric < 0) {
            const message = `Value should be number in row ${rowIndex + 2}.`;
            this._markInvalid(cell, message);
            errors.push(message);
          }
        }
      }.bind(this),
    );

    this.validationErrors = errors;
  }

  _saveReport() {
    this._validateTable();
    if (this.validationErrors.length > 0) {
      this.model.saveError = "Fix validation errors before saving.";
      this.model.saveSuccess = null;
      return;
    }

    if (!this.model.distributionParameter) {
      this.model.saveError = "Distribution parameter is required for saving.";
      this.model.saveSuccess = null;
      return;
    }

    this.model
      .saveReport(this.model.buildSavePayload())
      .then(function () {
        this.validationErrors = [];
        this._fetchReport();
      }.bind(this))
      .catch(function () {});
  }

  view() {
    const tableState = this._buildTableFromMatrix();

    return m(
      ".container-fluid.pt-4.px-4",
      [
        m(".row.g-4", [
          m(
            ".col-sm-12.col-md-6.col-xl-4",
            m(".h-100.bg-light.rounded.p-4", [
              m(
                ".d-flex.align-items-center.justify-content-between.mb-4",
                m("h6.mb-0", "Date Range"),
              ),
              m(".row.g-2", [
                m(
                  ".col-12",
                  m("input.form-control", {
                    type: "date",
                    value: this.model.filter.periodStart || "",
                    oninput: function (event) {
                      this.model.filter.periodStart = event.target.value;
                      this._fetchReport();
                    }.bind(this),
                  }),
                ),
                m(
                  ".col-12",
                  m("input.form-control", {
                    type: "date",
                    value: this.model.filter.periodEnd || "",
                    oninput: function (event) {
                      this.model.filter.periodEnd = event.target.value;
                      this._fetchReport();
                    }.bind(this),
                  }),
                ),
              ]),
            ]),
          ),
          m(
            ".col-sm-12.col-md-6.col-xl-4",
            m(".h-100.bg-light.rounded.p-4", [
              m(
                ".d-flex.align-items-center.justify-content-between.mb-4",
                m("h6.mb-0", "Campaign"),
              ),
              m(
                ".d-flex.mb-2",
                m(
                  "select.form-select.mb-3",
                  {
                    "aria-label": "Campaign",
                    oninput: function (event) {
                      this.model.filter.campaignId = Number(event.target.value);
                      this.model.distributionParameter = "";
                      this.model.distributionParameterLocked = false;
                      this.model.loadDistributionParameters(
                        this.model.filter.campaignId,
                      );
                      this.model.loadCampaignDetails(
                        this.model.filter.campaignId,
                      );
                      this._fetchReport();
                    }.bind(this),
                    value: this.model.filter.campaignId,
                  },
                  this.model.campaigns.map(function (campaign) {
                    return m("option", { value: campaign.id }, campaign.name);
                  }),
                ),
              ),
            ]),
          ),
          m(
            ".col-sm-12.col-md-6.col-xl-4",
            m(".h-100.bg-light.rounded.p-4", [
              m(
                ".d-flex.align-items-center.justify-content-between.mb-4",
                m("h6.mb-0", "Distribution Parameter"),
              ),
              m(".mb-3", [
                m(
                  "div.autocomplete",
                  {
                    oncreate: function (node) {
                      this.initDistributionParameterAutocomplete(node.dom);
                    }.bind(this),
                  },
                  [
                    m("input.form-control", {
                      type: "text",
                      value: this.model.distributionParameter,
                      placeholder: "Select distribution parameter",
                      readonly: this.model.distributionParameterLocked,
                      oninput: function (event) {
                        this.model.distributionParameter = event.target.value;
                        this.model.saveError = null;
                        this.model.saveSuccess = null;
                      }.bind(this),
                    }),
                    m(
                      "div",
                      { style: "position: relative;" },
                      m("ul.autocomplete-result-list"),
                    ),
                  ],
                ),
              ]),
              this.model.distributionParameterError
                ? m(
                    "div.text-danger.small.mt-2",
                    this.model.distributionParameterError,
                  )
                : null,
              this.model.distributionParameterValuesError
                ? m(
                    "div.text-danger.small.mt-2",
                    this.model.distributionParameterValuesError,
                  )
                : null,
            ]),
          ),
        ]),
        this.model.matrix !== null
          ? m(".row.g-4.mt-1", [
              m(".col-12", [
                m(".bg-light.rounded.p-4", [
                  m(
                    ".d-flex.align-items-center.justify-content-between.mb-3",
                    m("h6.mb-0", "Expenses Report"),
                  ),
                  this.model.error
                    ? m("div.text-danger.mb-3", this.model.error)
                    : null,
                  this.model.isLoading
                    ? m("div.mb-3", "Loading report...")
                    : null,
                  m(ExpensesReportTable, {
                    columns: tableState.columns,
                    rows: tableState.rows,
                    onReady: function (table) {
                      this.table = table;
                      this._validateTable();
                    }.bind(this),
                    onValidate: function () {
                      this._validateTable();
                    }.bind(this),
                    onChange: function (table, state) {
                      this.model.matrix = this._tableToMatrix(table);
                      const newEmptyCellsAdded =
                        this.model.ensureMinimumEmptySpace();

                      if (newEmptyCellsAdded) {
                        state.isSyncing = true;
                        this._refreshTableAppearance().then(function () {
                          state.isSyncing = false;
                        });
                      }
                    }.bind(this),
                  }),
                  m(".mt-3", [
                    m(".d-flex.flex-column.flex-md-row.gap-2", [
                      m(
                        "button.btn.btn-primary",
                        {
                          type: "button",
                          disabled:
                            this.model.isSaving ||
                            this.validationErrors.length > 0,
                          onclick: function () {
                            this._saveReport();
                          }.bind(this),
                        },
                        this.model.isSaving ? "Saving..." : "Save Report",
                      ),
                      m(
                        "button.btn.btn-outline-secondary",
                        {
                          type: "button",
                          onclick: function () {
                            this._resetToOriginal();
                          }.bind(this),
                        },
                        "Reset",
                      ),
                    ]),
                    this.validationErrors.length > 0
                      ? m(
                          "div.text-danger.mt-2",
                          `Validation errors: ${this.validationErrors.length}`,
                        )
                      : null,
                    this.model.saveError
                      ? m("div.text-danger.mt-2", this.model.saveError)
                      : null,
                    this.model.saveSuccess
                      ? m("div.text-success.mt-2", this.model.saveSuccess)
                      : null,
                  ]),
                ]),
              ]),
            ])
          : null,
      ],
    );
  }
}

module.exports = ExpensesReportView;
