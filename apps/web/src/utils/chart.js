class ChartUtils {
  static getClicks(statisticsContainer, groupParameters) {
    if (groupParameters.length === 0) {
      return statisticsContainer.clicks;
    }

    let distribution = {};
    for (const [distributionValue, stats] of Object.entries(statisticsContainer)) {
      if (stats !== null && typeof stats === "object") {
        distribution[distributionValue] = ChartUtils.getClicks(stats, groupParameters.slice(1));
      }
    }

    return distribution;
  }

  static getLeads(statisticsContainer, groupParameters, status) {
    if (typeof status === "undefined") {
      status = null;
    }

    if (groupParameters.length === 0) {
      if (status !== null) {
        return statisticsContainer.statuses[status].leads;
      }

      return Object.values(statisticsContainer.statuses)
        .map(function (container) {
          return container.leads;
        })
        .reduce(function (a, leads) {
          return a + leads;
        }, 0);
    }

    let distribution = {};
    for (const [distributionValue, stats] of Object.entries(statisticsContainer)) {
      if (stats !== null && typeof stats === "object") {
        distribution[distributionValue] = ChartUtils.getLeads(stats, groupParameters.slice(1), status);
      }
    }

    return distribution;
  }

  static getPayouts(statisticsContainer, groupParameters, expected) {
    if (typeof expected === "undefined") {
      expected = false;
    }

    if (groupParameters.length === 0) {
      let payouts = 0;

      if (Object.hasOwn(statisticsContainer.statuses, "accept")) {
        payouts += statisticsContainer.statuses.accept.payouts;
      }

      if (expected && Object.hasOwn(statisticsContainer.statuses, "expect")) {
        payouts += statisticsContainer.statuses.expect.payouts;
      }

      return payouts;
    }

    let distribution = {};
    for (const [distributionValue, stats] of Object.entries(statisticsContainer)) {
      if (stats !== null && typeof stats === "object") {
        distribution[distributionValue] = ChartUtils.getPayouts(stats, groupParameters.slice(1), expected);
      }
    }

    return distribution;
  }

  static getExpenses(statisticsContainer) {
    if (Object.hasOwn(statisticsContainer, "expenses")) {
      return statisticsContainer.expenses;
    }

    let distribution = {};
    for (const [distributionValue, stats] of Object.entries(statisticsContainer)) {
      if (stats !== null && typeof stats === "object") {
        distribution[distributionValue] = ChartUtils.getExpenses(stats);
      }
    }

    return distribution;
  }

  static getProfit(statisticsContainer, groupParameters, expected) {
    if (typeof expected === "undefined") {
      expected = false;
    }

    if (groupParameters.length === 0) {
      const key = expected ? "profit_expected" : "profit_accepted";
      return statisticsContainer[key];
    }

    let distribution = {};
    for (const [distributionValue, stats] of Object.entries(statisticsContainer)) {
      if (stats !== null && typeof stats === "object") {
        distribution[distributionValue] = ChartUtils.getProfit(stats, groupParameters.slice(1), expected);
      }
    }

    return distribution;
  }

  static getRoi(payout, expense) {
    if (typeof payout === "object" && typeof expense === "object") {
      let distribution = {};

      for (const [distributionValue, stats] of Object.entries(payout)) {
        distribution[distributionValue] = ChartUtils.getRoi(stats, expense[distributionValue]);
      }

      return distribution;
    }

    if (typeof payout === "object" && typeof expense === "number") {
      payout = Object.values(payout).reduce(function (a, payoutValue) {
        return a + payoutValue;
      }, 0);
    }

    if (expense === 0) {
      return 0;
    }

    return ((payout - expense) / expense) * 100;
  }

  static distribution2ChartJsDataset(distribution, defaultLabel) {
    if (distribution.every(function (el) { return typeof el === "number"; })) {
      return [
        {
          label: defaultLabel,
          data: distribution,
          fill: true,
          cubicInterpolationMode: "monotone",
        },
      ];
    }

    const datasets = {};

    for (const i in distribution) {
      const statisticsContainer = distribution[i];
      for (const [distributionValue, value] of Object.entries(statisticsContainer)) {
        if (!Object.hasOwn(datasets, distributionValue)) {
          datasets[distributionValue] = [];
        }

        datasets[distributionValue].push(value);
      }
    }

    const datasetsChartJs = [];
    for (const [distributionValue, dataset] of Object.entries(datasets)) {
      datasetsChartJs.push({
        label: distributionValue,
        data: dataset,
        fill: true,
        cubicInterpolationMode: "monotone",
      });
    }

    return datasetsChartJs;
  }
}

module.exports = ChartUtils;
