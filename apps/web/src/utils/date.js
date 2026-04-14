function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function normalizeTimestamp(value) {
  if (value === null || typeof value === "undefined") {
    return null;
  }

  let numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return value;
  }

  return numeric < 1000000000000 ? numeric * 1000 : numeric;
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

function formatOffset(offsetMinutes) {
  if (offsetMinutes === 0) {
    return "GMT+0";
  }

  let sign = offsetMinutes >= 0 ? "+" : "-";
  let absoluteMinutes = Math.abs(offsetMinutes);
  let hours = Math.floor(absoluteMinutes / 60);
  let minutes = absoluteMinutes % 60;

  if (minutes === 0) {
    return `GMT${sign}${hours}`;
  }

  return `GMT${sign}${hours}:${pad2(minutes)}`;
}

function formatDateTimeParts(year, month, day, hours, minutes, seconds, suffix) {
  return `${year}-${pad2(month)}-${pad2(day)} ${pad2(hours)}:${pad2(minutes)}:${pad2(seconds)} ${suffix}`;
}

function timestamp2LocalTime(value) {
  let timestamp = normalizeTimestamp(value);

  if (timestamp === null) {
    return "-";
  }

  if (typeof timestamp !== "number") {
    return String(timestamp);
  }

  let date = new Date(timestamp);
  let offsetMinutes = -date.getTimezoneOffset();

  return formatDateTimeParts(
    date.getFullYear(),
    date.getMonth() + 1,
    date.getDate(),
    date.getHours(),
    date.getMinutes(),
    date.getSeconds(),
    formatOffset(offsetMinutes),
  );
}

function timestamp2UtcTime(value) {
  let timestamp = normalizeTimestamp(value);

  if (timestamp === null) {
    return "-";
  }

  if (typeof timestamp !== "number") {
    return String(timestamp);
  }

  let date = new Date(timestamp);

  return formatDateTimeParts(
    date.getUTCFullYear(),
    date.getUTCMonth() + 1,
    date.getUTCDate(),
    date.getUTCHours(),
    date.getUTCMinutes(),
    date.getUTCSeconds(),
    "UTC",
  );
}

function setDefaultDateRange(target, startKey, endKey) {
  if (target[startKey] && target[endKey]) {
    return;
  }

  let today = new Date();
  let fromDate = new Date(today);
  fromDate.setDate(today.getDate() - 6);

  target[startKey] = formatDate(fromDate);
  target[endKey] = formatDate(today);
}

module.exports = {
  formatDate,
  timestamp2LocalTime,
  timestamp2UtcTime,
  setDefaultDateRange,
};
