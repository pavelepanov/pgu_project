export function getTelegram() {
  return window.Telegram?.WebApp ?? null;
}

export function isTelegram() {
  return Boolean(getTelegram()?.initData);
}

export function getInitData() {
  return getTelegram()?.initData || "";
}

export function expandApp() {
  const telegram = getTelegram();
  if (!telegram) return;
  telegram.ready();
  telegram.expand();
}

export function hapticImpact(style = "light") {
  getTelegram()?.HapticFeedback?.impactOccurred(style);
}
