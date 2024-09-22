import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LoginPage from './components/Login';
import RegisterPage from './components/Registration';
import ProfilePage from './components/ProfilePage';
import Header from './components/Header';
import jwtDecode from 'jwt-decode';
import { getUserProfile } from './api';
import './styles/App.css';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);


  
  const fetchUserProfile = async () => {
    try {
      // Извлечение токена из куки
      const token = document.cookie.split('; ').find(row => row.startsWith('auth_token='));
      if (token) {
        // Удаление префикса 'auth_token='
        const tokenValue = token.split('=')[1];
        
        // Декодирование токена
        const decodedToken = jwtDecode(tokenValue);
        const userId = decodedToken.sub; // Извлечь ID пользователя из декодированного токена
  
        // Получение профиля пользователя
        const userData = await getUserProfile(userId);
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        // Нет токена, пользователь не авторизован
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
      setIsAuthenticated(false);
    }
  };
  
  useEffect(() => {
    fetchUserProfile();
  }, []);

  return (
    <Router>
      <Header isAuthenticated={isAuthenticated} user={user} />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
    </Router>
  );
};

export default App;