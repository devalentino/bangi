const api = require("./api");
var config = require("../config");

class ExpensesReportFilter {
  constructor() {
    this.periodStart = null;
    this.periodEnd = null;
    this.campaignId = null;
  }

  isReady() {
    return (
      this.periodStart !== null &&
      this.periodEnd !== null &&
      this.campaignId !== null
    );
  }
}

class ExpensesReportModel {
  constructor() {
    this.filter = new ExpensesReportFilter();
    this.records = [];
    this.matrix = null;
    this.campaigns = [];
    this.campaignError = null;
    this.distributionParameter = "";
    this.distributionParameterError = null;
    this.distributionParameterLocked = false;
    this.distributionParameters = [];
    this.distributionParameterValuesError = null;
    this.isLoading = false;
    this.error = null;
    this.isSaving = false;
    this.saveError = null;
    this.saveSuccess = null;
  }

  loadExpensesReport() {
    if (!this.filter.isReady()) {
      return Promise.resolve();
    }

    const startMs = Date.parse(this.filter.periodStart);
    const endMs = Date.parse(this.filter.periodEnd);
    let pageSize = 1;

    if (!Number.isNaN(startMs) && !Number.isNaN(endMs)) {
      const diffDays = Math.floor((endMs - startMs) / 86400000) + 1;
      pageSize = Math.max(1, diffDays);
    }

    this.isLoading = true;
    this.error = null;

    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/reports/expenses`,
        params: {
          periodStart: this.filter.periodStart,
          periodEnd: this.filter.periodEnd,
          campaignId: this.filter.campaignId,
          page: 1,
          pageSize: pageSize,
          sortBy: "date",
          sortOrder: "asc",
        },
      })
      .then(function (payload) {
        this.records = payload.content;
        this.isLoading = false;
        this._buildMatrix();
      }.bind(this))
      .catch(function () {
        this.error = "Failed to load expenses report.";
        this.isLoading = false;
      }.bind(this));
  }

  loadCampaigns() {
    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/core/campaigns`,
      })
      .then(function (payload) {
        this.campaigns = payload.content;
        this.campaignError = null;
      }.bind(this))
      .catch(function () {
        this.campaigns = [];
        this.campaignError = "Failed to load campaigns.";
      }.bind(this));
  }

  loadDistributionParameters(campaignId) {
    if (!campaignId) {
      this.distributionParameters = [];
      return Promise.resolve();
    }

    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/reports/helpers/expenses-distribution-parameters`,
        params: {
          campaignId: campaignId,
        },
      })
      .then(function (payload) {
        this.distributionParameters = payload;
        this.distributionParameterError = null;
      }.bind(this))
      .catch(function () {
        this.distributionParameters = [];
        this.distributionParameterError =
          "Failed to load distribution parameters.";
      }.bind(this));
  }

  loadDistributionParameterValues(campaignId, parameter) {
    if (!campaignId || !parameter) {
      return Promise.resolve();
    }

    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/reports/helpers/expenses-distribution-parameter-values`,
        params: {
          campaignId: campaignId,
          parameter: parameter,
        },
      })
      .then(function (payload) {
        const values = (payload).map(function (item) {
          return item.value;
        });
        this.setHeaderKeys(values);
        this.distributionParameterValuesError = null;
      }.bind(this))
      .catch(function () {
        this.distributionParameterValuesError =
          "Failed to load distribution parameter values.";
      }.bind(this));
  }

  loadCampaignDetails(campaignId) {
    if (!campaignId) {
      this.distributionParameterLocked = false;
      return Promise.resolve();
    }

    return api
      .request({
        method: "GET",
        url: `${config.backendApiBaseUrl}/core/campaigns/${campaignId}`,
      })
      .then(function (payload) {
        this.distributionParameter = payload.expensesDistributionParameter;
        this.distributionParameterLocked = this.distributionParameter !== null;
        return null;
      }.bind(this))
      .catch(function () {
        this.distributionParameterLocked = false;
      }.bind(this));
  }

  saveReport(payload) {
    this.isSaving = true;
    this.saveError = null;
    this.saveSuccess = null;

    return api
      .request({
        method: "POST",
        url: `${config.backendApiBaseUrl}/reports/expenses`,
        body: payload,
      })
      .then(function () {
        this.isSaving = false;
        this.saveSuccess = "Report saved.";
      }.bind(this))
      .catch(function () {
        this.isSaving = false;
        this.saveError = "Failed to save report.";
      }.bind(this));
  }

  _buildMatrix() {
    const distributionKeySet = new Set();

    this.records.forEach(function (record) {
      const distribution = record.distribution || {};
      Object.keys(distribution).forEach(function (key) {
        distributionKeySet.add(key);
      });
    });

    const distributionKeys = Array.from(distributionKeySet).sort(function (
      a,
      b,
    ) {
      return a.localeCompare(b);
    });

    const width = Math.max(1, distributionKeys.length + 1);

    const headerRow = new Array(width).fill(null);
    distributionKeys.forEach(function (key, index) {
      headerRow[index + 1] = key;
    });

    const rows = this.records.map(function (record) {
      const row = new Array(width).fill(null);
      row[0] = record.date || null;

      const distribution = record.distribution || {};
      distributionKeys.forEach(function (key, index) {
        if (Object.prototype.hasOwnProperty.call(distribution, key)) {
          row[index + 1] = distribution[key];
        }
      });

      return row;
    });

    this.matrix = [headerRow].concat(rows);

    this._ensureEmptyRows();
    this._ensureEmptyColumns();
  }

  _isRowEmpty(row) {
    return row.every(function (value) {return value === null});
  }

  _ensureEmptyRows() {
    let emptyTrailingRows = 0;

    for (let i = this.matrix.length - 1; i >= 1 && emptyTrailingRows < 2; i -= 1) {
      if (this._isRowEmpty(this.matrix[i])) {
        emptyTrailingRows += 1;
      } else {
        break;
      }
    }

    while (emptyTrailingRows < 2) {
      const row = new Array(this._matrixColumnCount()).fill(null);
      this.matrix.push(row);
      emptyTrailingRows += 1;
    }
  }

  _ensureEmptyColumns() {
    if (this.matrix.length === 0) {
      this.matrix = [new Array(1).fill(null)];
    }

    const headerRow = this.matrix[0] || [];
    let trailingEmptyColumns = 0;

    for (let i = headerRow.length - 1; i >= 1 && trailingEmptyColumns < 2; i -= 1) {
      const value = headerRow[i];
      if (value === null) {
        trailingEmptyColumns += 1;
      } else {
        break;
      }
    }

    if (trailingEmptyColumns >= 2) {
      return;
    }

    const needed = 2 - trailingEmptyColumns;

    this.matrix.forEach(function (row) {
      for (let i = 0; i < needed; i += 1) {
        row.push(null);
      }
    });
  }

  ensureMinimumEmptySpace() {
    const previousColumnCount = this._matrixColumnCount();
    const previousRowCount = this.matrix.length;

    this._ensureEmptyColumns();
    this._ensureEmptyRows();

    return (
      previousColumnCount !== this._matrixColumnCount() ||
      previousRowCount !== this.matrix.length
    );
  }

  resetToOriginal() {
    this._buildMatrix();
  }

  _matrixColumnCount() {
    if (!this.matrix || this.matrix.length === 0) {
      return 1;
    }

    return Math.max(1, this.matrix[0].length);
  }

  setHeaderKeys(keys) {
    const safeKeys = Array.isArray(keys) ? keys : [];
    const baseWidth = Math.max(1, safeKeys.length + 1);

    if (!this.matrix || this.matrix.length === 0) {
      this.matrix = [new Array(baseWidth).fill(null)];
    }

    const headerRow = new Array(baseWidth).fill(null);
    safeKeys.forEach(function (key, index) {
      headerRow[index + 1] = key;
    });

    this.matrix[0] = headerRow;

    for (let i = 1; i < this.matrix.length; i += 1) {
      const row = this.matrix[i];
      if (row.length < baseWidth) {
        while (row.length < baseWidth) {
          row.push(null);
        }
      } else if (row.length > baseWidth) {
        row.length = baseWidth;
      }
      this.matrix[i] = row;
    }

    this._ensureEmptyRows();
    this._ensureEmptyColumns();
  }

  buildSavePayload() {
    const headerRow = this.matrix[0];
    const columnCount = headerRow.length;

    const dates = this.matrix
      .slice(1)
      .filter(function (row) {return row && row[0] !== null})
      .map(function (row) {
        const distribution = {};

        for (let i = 1; i < columnCount; i += 1) {
          if (headerRow[i] === null) {
            continue;
          }

          const key = headerRow[i].trim();
          distribution[key] = row[i];
        }

        return {
          date: row[0],
          distribution: distribution,
        };
      });

    return {
      campaignId: Number(this.filter.campaignId),
      distributionParameter: this.distributionParameter,
      dates: dates,
    };
  }
}

module.exports = ExpensesReportModel;
