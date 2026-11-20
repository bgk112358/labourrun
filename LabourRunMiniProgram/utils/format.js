function pad(value) {
  return value < 10 ? '0' + value : String(value);
}

function formatTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (isNaN(date.getTime())) return String(value);
  return (
    date.getFullYear() +
    '-' +
    pad(date.getMonth() + 1) +
    '-' +
    pad(date.getDate()) +
    ' ' +
    pad(date.getHours()) +
    ':' +
    pad(date.getMinutes()) +
    ':' +
    pad(date.getSeconds())
  );
}

function formatMoney(value) {
  if (value === undefined || value === null || value === '') {
    return '0.00';
  }
  return String(value);
}

function statusText(status) {
  if (status === 'registered') return '已报名';
  if (status === 'cancelled') return '已取消';
  if (status === 'upcoming') return '未开始';
  if (status === 'ongoing') return '进行中';
  if (status === 'ended') return '已结束';
  return status || '';
}

module.exports = {
  formatTime,
  formatMoney,
  statusText,
};
