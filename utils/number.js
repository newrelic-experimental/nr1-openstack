exports.defaultFormatted = num =>
  (num === 0 || (num && !Number.isNaN(num))) ? new Intl.NumberFormat('default', {
    style: 'decimal',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num) : '';

exports.percentFormatted = num =>
  (num && !Number.isNaN(num)) ? new Intl.NumberFormat('default', {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num / 100) : '';

// for available units, see:
// https://tc39.es/proposal-unified-intl-numberformat/section6/locales-currencies-tz_proposed_out.html#table-sanctioned-simple-unit-identifiers

exports.unitFormatted = (num, type) =>
  new Intl.NumberFormat('default', {
    style: 'unit',
    unit: type,
    maximumFractionDigits: 2
  }).format(num);
