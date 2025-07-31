// Debug script to check frontend authentication state
// Run this in the browser console when on the frontend

console.log('=== Frontend Authentication Debug ===');

// Check localStorage tokens
const accessToken = localStorage.getItem('access_token');
const refreshToken = localStorage.getItem('refresh_token');

console.log('Access Token:', accessToken ? 'Present' : 'Missing');
console.log('Refresh Token:', refreshToken ? 'Present' : 'Missing');

if (accessToken) {
  try {
    // Decode JWT token (basic decode, not verification)
    const payload = JSON.parse(atob(accessToken.split('.')[1]));
    console.log('Token Payload:', payload);
    console.log('Token Expires:', new Date(payload.exp * 1000));
    console.log('Token Valid:', new Date() < new Date(payload.exp * 1000));
  } catch (e) {
    console.log('Token Decode Error:', e.message);
  }
}

// Check current URL and authentication state
console.log('Current URL:', window.location.href);
console.log('Current Path:', window.location.pathname);
console.log('URL Params:', window.location.search);

// Test API call
if (accessToken) {
  console.log('Testing API call...');
  fetch('/api/users/api-keys/providers', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    console.log('API Response Status:', response.status);
    if (response.ok) {
      return response.json();
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  })
  .then(data => {
    console.log('API Response Data:', data);
    console.log('✅ API call successful!');
  })
  .catch(error => {
    console.log('❌ API call failed:', error.message);
  });
} else {
  console.log('❌ No access token - cannot test API');
}

// Check if user is on the correct page
if (window.location.pathname === '/dashboard' && window.location.search.includes('view=api-keys')) {
  console.log('✅ On API Keys management page');
} else {
  console.log('ℹ️ Not on API Keys management page');
  console.log('To access API Keys: http://localhost:3000/dashboard?view=api-keys');
}

console.log('=== End Debug ===');