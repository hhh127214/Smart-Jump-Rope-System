const BASE = "/api/admin";

async function r(url, options = {}) {
  const token = localStorage.getItem("admin_token");
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, { ...options, headers });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail || json.message || `HTTP ${res.status}`);
  return json;
}

export const api = {
  // Auth
  login: (data) => r(`${BASE}/auth/login`, { method: "POST", body: JSON.stringify(data) }),
  logout: () => r(`${BASE}/auth/logout`, { method: "POST" }),
  me: () => r(`${BASE}/auth/me`),

  // Dashboard
  dashboardStats: () => r(`${BASE}/dashboard/stats`),
  dashboardTrend: (days) => r(`${BASE}/dashboard/trend?days=${days}`),

  // Schools
  schools: (params) => r(`${BASE}/schools?` + new URLSearchParams(params)),
  schoolCreate: (data) => r(`${BASE}/schools`, { method: "POST", body: JSON.stringify(data) }),
  schoolUpdate: (id, data) => r(`${BASE}/schools/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  schoolDelete: (id) => r(`${BASE}/schools/${id}`, { method: "DELETE" }),

  // Grades
  grades: (params) => r(`${BASE}/grades?` + new URLSearchParams(params)),
  gradeCreate: (data) => r(`${BASE}/grades`, { method: "POST", body: JSON.stringify(data) }),
  gradeUpdate: (id, data) => r(`${BASE}/grades/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  gradeDelete: (id) => r(`${BASE}/grades/${id}`, { method: "DELETE" }),

  // Classes
  classes: (params) => r(`${BASE}/classes?` + new URLSearchParams(params)),
  classCreate: (data) => r(`${BASE}/classes`, { method: "POST", body: JSON.stringify(data) }),
  classUpdate: (id, data) => r(`${BASE}/classes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  classDelete: (id) => r(`${BASE}/classes/${id}`, { method: "DELETE" }),

  // Students
  students: (params) => r(`${BASE}/students?` + new URLSearchParams(params)),
  studentCreate: (data) => r(`${BASE}/students`, { method: "POST", body: JSON.stringify(data) }),
  studentUpdate: (id, data) => r(`${BASE}/students/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  studentDelete: (id) => r(`${BASE}/students/${id}`, { method: "DELETE" }),
  studentDetail: (id) => r(`${BASE}/students/${id}`),

  // Venues
  venues: (params) => r(`${BASE}/venues?` + new URLSearchParams(params)),
  venueCreate: (data) => r(`${BASE}/venues`, { method: "POST", body: JSON.stringify(data) }),
  venueUpdate: (id, data) => r(`${BASE}/venues/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  venueDelete: (id) => r(`${BASE}/venues/${id}`, { method: "DELETE" }),

  // Devices
  devices: (params) => r(`${BASE}/devices?` + new URLSearchParams(params)),
  deviceCreate: (data) => r(`${BASE}/devices`, { method: "POST", body: JSON.stringify(data) }),
  deviceUpdate: (id, data) => r(`${BASE}/devices/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deviceDelete: (id) => r(`${BASE}/devices/${id}`, { method: "DELETE" }),

  // Tasks
  tasks: (params) => r(`${BASE}/tasks?` + new URLSearchParams(params)),
  taskCreate: (data) => r(`${BASE}/tasks`, { method: "POST", body: JSON.stringify(data) }),
  taskUpdate: (id, data) => r(`${BASE}/tasks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  taskPublish: (id) => r(`${BASE}/tasks/${id}/publish`, { method: "POST" }),
  taskCancel: (id) => r(`${BASE}/tasks/${id}/cancel`, { method: "POST" }),

  // Scores
  scores: (params) => r(`${BASE}/scores?` + new URLSearchParams(params)),
  scoreDetail: (id) => r(`${BASE}/scores/${id}`),
  scoreReview: (id, data) => r(`${BASE}/scores/${id}/review`, { method: "PUT", body: JSON.stringify(data) }),
  scoreBatchReview: (data) => r(`${BASE}/scores/batch-review`, { method: "POST", body: JSON.stringify(data) }),
  scoreStats: (params) => r(`${BASE}/scores/stats?` + new URLSearchParams(params)),

  // Exceptions
  exceptions: (params) => r(`${BASE}/exceptions?` + new URLSearchParams(params)),
  exceptionResolve: (id, data) => r(`${BASE}/exceptions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  exceptionBatchResolve: (data) => r(`${BASE}/exceptions/batch`, { method: "POST", body: JSON.stringify(data) }),

  // Settings
  settings: () => r(`${BASE}/settings`),
  settingsUpdate: (data) => r(`${BASE}/settings`, { method: "PUT", body: JSON.stringify(data) }),

  // Logs
  operationLogs: (params) => r(`${BASE}/logs/operation?` + new URLSearchParams(params)),
  loginLogs: (params) => r(`${BASE}/logs/login?` + new URLSearchParams(params)),
};
