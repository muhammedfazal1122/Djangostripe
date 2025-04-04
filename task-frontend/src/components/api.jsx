const BASE_URL = "http://127.0.0.1:8000";
// src/api.js
const API_URL = "http://localhost:8000/api"; // adjust if needed

export async function login(username, password) {
  const res = await fetch(`${API_URL}/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return await res.json();
}

export async function register(username, password) {
  const res = await fetch(`${API_URL}/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
