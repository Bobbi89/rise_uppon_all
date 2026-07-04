// Integrazione client del Revolut Merchant Web SDK.
// Il popup di pagamento mostra automaticamente carta, Revolut Pay e Apple Pay
// (se disponibili sul dispositivo e abilitati sull'account merchant).

type RevolutInstance = {
  payWithPopup(opts: {
    onSuccess?: () => void;
    onError?: (error: { message?: string }) => void;
    onCancel?: () => void;
  }): void;
  destroy?(): void;
};

type RevolutCheckoutFn = (
  token: string,
  mode: "sandbox" | "prod",
) => Promise<RevolutInstance>;

declare global {
  interface Window {
    RevolutCheckout?: RevolutCheckoutFn;
  }
}

function scriptUrl(mode: "sandbox" | "prod"): string {
  return mode === "prod"
    ? "https://merchant.revolut.com/embed.js"
    : "https://sandbox-merchant.revolut.com/embed.js";
}

function loadSdk(mode: "sandbox" | "prod"): Promise<void> {
  if (window.RevolutCheckout) return Promise.resolve();
  const src = scriptUrl(mode);
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Impossibile caricare Revolut")));
      return;
    }
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Impossibile caricare Revolut"));
    document.head.appendChild(s);
  });
}

export type RevolutOutcome = "success" | "cancel";

/** Apre il popup Revolut per pagare l'ordine identificato dal token pubblico. */
export async function payWithRevolut(
  token: string,
  mode: "sandbox" | "prod",
): Promise<RevolutOutcome> {
  await loadSdk(mode);
  if (!window.RevolutCheckout) throw new Error("Revolut non disponibile");
  const instance = await window.RevolutCheckout(token, mode);
  return new Promise<RevolutOutcome>((resolve, reject) => {
    instance.payWithPopup({
      onSuccess: () => {
        instance.destroy?.();
        resolve("success");
      },
      onCancel: () => {
        instance.destroy?.();
        resolve("cancel");
      },
      onError: (error) => {
        instance.destroy?.();
        reject(new Error(error?.message || "Pagamento non riuscito"));
      },
    });
  });
}
