const BASE_URL = "http://127.0.0.1:8000";
// src/api.jsconst
const API_BASE = "http://localhost:8000/api"; // Update if your backend runs on a different port or URL

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/token/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  return await res.json();
}

export async function register(username, password) {
  const res = await fetch(`${API_BASE}/register/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  return await res.json();
}



export const getTasks = async (token) => {
  const res = await fetch(`${BASE_URL}/api/tasks/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
};

export const createTask = async (token, data) => {
  const res = await fetch(`${BASE_URL}/api/tasks/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return res.json();
};

export const deleteTask = async (token, id) => {
  return fetch(`${BASE_URL}/api/tasks/${id}/`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};

export const getMetering = async (token) => {
  const res = await fetch(`${BASE_URL}/api/metering/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
};
