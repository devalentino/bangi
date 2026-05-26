var m = require("mithril");
var en = require("./locales/en.json");
var uk = require("./locales/uk.json");

var STORAGE_KEY = "bangi.locale";
var DEFAULT_LOCALE = "en";
var catalogs = { en: en, uk: uk };
var currentLocale = resolveInitialLocale();

function getStorage() {
  if (typeof localStorage === "undefined") {
    return null;
  }

  return localStorage;
}

function normalizeLocale(locale) {
  if (!locale || typeof locale !== "string") {
    return null;
  }

  var normalized = locale.toLowerCase();
  if (normalized === "uk" || normalized.indexOf("uk-") === 0) {
    return "uk";
  }
  if (normalized === "en" || normalized.indexOf("en-") === 0) {
    return "en";
  }

  return null;
}

function getBrowserLanguages() {
  if (typeof navigator === "undefined") {
    return [];
  }

  if (navigator.languages && navigator.languages.length) {
    return navigator.languages;
  }
  if (navigator.language) {
    return [navigator.language];
  }

  return [];
}

function resolveLocale(options) {
  var opts = options || {};
  var storedLocale = normalizeLocale(opts.storedLocale);
  if (storedLocale) {
    return storedLocale;
  }

  var languages = opts.languages || [];
  for (var index = 0; index < languages.length; index += 1) {
    var browserLocale = normalizeLocale(languages[index]);
    if (browserLocale) {
      return browserLocale;
    }
  }

  return DEFAULT_LOCALE;
}

function resolveInitialLocale() {
  var storage = getStorage();
  return resolveLocale({
    storedLocale: storage ? storage.getItem(STORAGE_KEY) : null,
    languages: getBrowserLanguages(),
  });
}

function getLocale() {
  return currentLocale;
}

function setLocale(locale) {
  var normalized = normalizeLocale(locale) || DEFAULT_LOCALE;
  currentLocale = normalized;

  var storage = getStorage();
  if (storage) {
    storage.setItem(STORAGE_KEY, normalized);
  }

  if (m && typeof m.redraw === "function") {
    m.redraw();
  }
}

function formatMessage(message, values) {
  if (!values) {
    return message;
  }

  return message.replace(/\{([^}]+)\}/g, function (match, key) {
    return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : match;
  });
}

function t(key, values) {
  var catalog = catalogs[currentLocale] || catalogs[DEFAULT_LOCALE];
  var message = catalog[key] || catalogs[DEFAULT_LOCALE][key];

  if (!message) {
    if (
      typeof process === "undefined" ||
      !process.env ||
      process.env.NODE_ENV !== "production"
    ) {
      return "[missing translation: " + key + "]";
    }
    return key;
  }

  return formatMessage(message, values);
}

function formatDate(value, options) {
  return new Intl.DateTimeFormat(currentLocale, options).format(value);
}

function formatNumber(value, options) {
  return new Intl.NumberFormat(currentLocale, options).format(value);
}

function formatCurrency(value, currency) {
  return formatNumber(value, { style: "currency", currency: currency });
}

module.exports = {
  DEFAULT_LOCALE: DEFAULT_LOCALE,
  STORAGE_KEY: STORAGE_KEY,
  formatCurrency: formatCurrency,
  formatDate: formatDate,
  formatNumber: formatNumber,
  getLocale: getLocale,
  normalizeLocale: normalizeLocale,
  resolveLocale: resolveLocale,
  setLocale: setLocale,
  t: t,
};
