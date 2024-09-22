import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Header.css';

const Header = ({ isAuthenticated, user }) => {
  return (
    <div className="header">
      <div className="header-right">
        {isAuthenticated ? (
          <Link to="/profile" className="user-info">
            <img src={user.photoURL} alt="User Avatar" className="user-avatar" />
            <span className="user-name">{user.username}</span>
          </Link>
        ) : (
          <div className="auth-links">
            <Link to="/login">Sign in</Link> | <Link to="/register">Sign up</Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Header;
