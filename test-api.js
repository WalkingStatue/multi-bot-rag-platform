// Simple test script to verify API endpoints
const testProfile = async () => {
  try {
    // First login to get token
    const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'testuser123',
        password: 'TestPassword123'
      })
    });

    const loginData = await loginResponse.json();
    console.log('Login successful, token:', loginData.access_token.substring(0, 50) + '...');

    // Then get profile
    const profileResponse = await fetch('http://localhost:8000/api/users/profile', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${loginData.access_token}`,
        'Content-Type': 'application/json',
      }
    });

    const profileData = await profileResponse.json();
    console.log('Profile Status:', profileResponse.status);
    console.log('Profile Response:', profileData);
  } catch (error) {
    console.error('Profile Error:', error);
  }
};

testProfile();