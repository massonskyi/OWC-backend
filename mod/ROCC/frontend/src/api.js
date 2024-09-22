import axios from 'axios';

export const signUp = async (data) => {
  try {
    const url = 'http://172.18.0.3:8050/sign_up';
    console.log('Request URL:', url);
    const response = await axios.post(url, data, { withCredentials: true });
    return response.data;
  } catch (error) {
    console.error('Sign Up Error:', error.response ? error.response.data : error.message);
    throw error;
  }
};

export const signIn = async (data) => {
  try {
    const url = 'http://172.18.0.3:8050/sign_in';
    console.log('Request URL:', url);
    const response = await axios.post(url, data, { withCredentials: true });
    return response.data;
  } catch (error) {
    console.error('Sign In Error:', error.response ? error.response.data : error.message);
    throw error;
  }
};


export const getUserProfile = async (userId) => {
  try {
    const url = `http://172.18.0.3:8050/profile/${userId}`;
    console.log('Request URL:', url);
    const response = await axios.get(url, { withCredentials: true });
    return response.data;
  } catch (error) {
    console.error('Get User Profile Error:', error.response ? error.response.data : error.message);
    throw error;
  }
};

export const updateUserProfile = async (userId, profileData) => {
  try {
    const url = `http://172.18.0.3:8050/profile/${userId}`;
    console.log('Request URL:', url);
    const response = await axios.put(url, profileData, { withCredentials: true });
    return response.data;
  } catch (error) {
    console.error('Update User Profile Error:', error.response ? error.response.data : error.message);
    throw error;
  }
};

export const deleteUserProfile = async (userId) => {
  try {
    const url = `http://172.18.0.3:8050/profile/${userId}`;
    console.log('Request URL:', url);
    await axios.delete(url, { withCredentials: true });
  } catch (error) {
    console.error('Delete User Profile Error:', error.response ? error.response.data : error.message);
    throw error;
  }
};