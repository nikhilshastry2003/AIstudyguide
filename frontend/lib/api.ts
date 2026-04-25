const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data as T;
}

export const api = {
  signup: (name: string, email: string, password: string) =>
    request<{ user_id: number; message: string }>('/signup', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email: string, password: string) =>
    request<{ user_id: number; message: string }>('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  createSubject: (user_id: number, subject_name: string) =>
    request<{ subject_id: number; message: string }>('/create-subject', {
      method: 'POST',
      body: JSON.stringify({ user_id, subject_name }),
    }),

  getSubjects: (user_id: number) =>
    request<{ subject_id: number; subject_name: string; created_at: string }[]>(
      `/my-subjects/${user_id}`
    ),

  createSession: (subject_id: number, title: string) =>
    request<{ session_id: number; message: string }>('/create-session', {
      method: 'POST',
      body: JSON.stringify({ subject_id, title }),
    }),

  getSessions: (subject_id: number) =>
    request<{ session_id: number; title: string; created_at: string }[]>(
      `/my-sessions/${subject_id}`
    ),

  getChats: (session_id: number) =>
    request<{ chat_id: number; question: string; answer: string; created_at: string }[]>(
      `/my-chats/${session_id}`
    ),

  runPipeline: (user_id: number, prompt: string) =>
    request<{
      guide: {
        overview: string;
        sections: { title: string; content: string }[];
        estimated_time_hours: number | null;
        prerequisites: string[];
        extra_tips: string[];
        sources: { provider: string; model: string; snippet: string }[];
      };
      job_id: number;
      provider_outputs: unknown[];
    }>('/pipeline/run', {
      method: 'POST',
      body: JSON.stringify({ user_id, prompt }),
    }),
};
