const BASE_URL = 'http://localhost:8000';

export const login = async (email: string) => {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  if (!res.ok) throw new Error('Login failed');
  return res.json();
};

export const getCustomerDetails = async (token: string) => {
  // We'll mock a call to the core banking API or through an agent
  // For the MVP, we assume the frontend just uses the token
  return { token };
};

export const confirmAction = async (actionId: string, token: string) => {
  const res = await fetch(`${BASE_URL}/actions/${actionId}/confirm`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}` 
    }
  });
  if (!res.ok) throw new Error('Action confirmation failed');
  return res.json();
};

export const cancelAction = async (actionId: string, token: string) => {
  const res = await fetch(`${BASE_URL}/actions/${actionId}/cancel`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}` 
    }
  });
  if (!res.ok) throw new Error('Action cancellation failed');
  return res.json();
};
