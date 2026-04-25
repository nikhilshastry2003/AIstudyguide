export function getUserId(): number | null {
  if (typeof window === 'undefined') return null;
  const id = localStorage.getItem('user_id');
  return id ? parseInt(id, 10) : null;
}

export function setAuth(userId: number, name: string): void {
  localStorage.setItem('user_id', String(userId));
  localStorage.setItem('user_name', name);
}

export function getUserName(): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('user_name') || 'User';
}

export function logout(): void {
  localStorage.removeItem('user_id');
  localStorage.removeItem('user_name');
}

export function isAuthenticated(): boolean {
  return getUserId() !== null;
}
