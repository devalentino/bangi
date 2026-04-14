var m = require("mithril");
var ChartJS = require("chart.js/auto");
var ChartColors = require("chart.js").Colors;

if (ChartColors) {
  ChartJS.register(ChartColors);
}

class Chart {
  constructor() {
    this.chartInstance = null;
  }

  oncreate({ dom, attrs }) {
    var ctx = dom.getContext("2d");
    this.chartInstance = new ChartJS(ctx, attrs.chartOptions);
  }

  onupdate({ attrs }) {
    if (this.chartInstance) {
      this.chartInstance.data = attrs.chartOptions.data;
      this.chartInstance.options = attrs.chartOptions.options;
      this.chartInstance.update();
    }
  }

  onremove() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  }

  view() {
    return m("canvas");
  }
}

module.exports = Chart;
