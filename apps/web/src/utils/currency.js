function formatCurrency(value, currency) {
  if (value === null || typeof value === "undefined") {
    return "-";
  }

  if (currency) {
    return `${value} ${String(currency).toUpperCase()}`;
  }

  return String(value);
}

module.exports = { formatCurrency };
