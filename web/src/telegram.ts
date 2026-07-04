// Wrapper tipizzato per il Telegram Web App SDK.
// Tutte le chiamate sono no-op sicure quando l'app gira fuori da Telegram.

type TelegramWebApp = {
  ready(): void;
  expand(): void;
  close(): void;
  isVersionAtLeast(version: string): boolean;
  setHeaderColor(color: string): void;
  setBackgroundColor(color: string): void;
  enableClosingConfirmation(): void;
  colorScheme: "light" | "dark";
  MainButton: {
    isVisible: boolean;
    show(): void;
    hide(): void;
    setText(text: string): void;
    setParams(params: { color?: string; text_color?: string }): void;
    onClick(callback: () => void): void;
    offClick(callback: () => void): void;
  };
  HapticFeedback?: {
    impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void;
    notificationOccurred(type: "error" | "success" | "warning"): void;
    selectionChanged(): void;
  };
  showAlert(message: string): void;
  sendData(data: string): void;
  openLink(url: string, options?: { try_instant_view?: boolean }): void;
  initData?: string;
  initDataUnsafe?: {
    user?: {
      id: number;
      first_name?: string;
      last_name?: string;
      username?: string;
    };
  };
};

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

export function getTelegram(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function initTelegram(): void {
  const tg = getTelegram();
  if (!tg) return;
  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor("#1f2e1f");
    tg.setBackgroundColor("#f7f4ec");
  } catch {
    // versioni vecchie del client non supportano i colori custom
  }
}

export function haptic(style: "light" | "medium" | "heavy" = "light"): void {
  getTelegram()?.HapticFeedback?.impactOccurred(style);
}

export function hapticSuccess(): void {
  getTelegram()?.HapticFeedback?.notificationOccurred("success");
}

export function telegramUserName(): string | null {
  const user = getTelegram()?.initDataUnsafe?.user;
  if (!user) return null;
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username || null;
}

/** initData firmato da Telegram: autentica l'utente verso l'API. */
export function telegramInitData(): string {
  return getTelegram()?.initData ?? "";
}

export function hapticError(): void {
  getTelegram()?.HapticFeedback?.notificationOccurred("error");
}
