export const ADMIN_KEY_STORAGE = "dailyDiet.adminKey";

export function getAdminKey(): string {
  return localStorage.getItem(ADMIN_KEY_STORAGE) ?? "";
}

export function setAdminKey(key: string): void {
  localStorage.setItem(ADMIN_KEY_STORAGE, key);
}
