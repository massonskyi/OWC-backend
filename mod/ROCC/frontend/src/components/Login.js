import React, { useState } from 'react';
import { Container } from './Shared/Container';
import { Input } from './Shared/Input';
import { AnimatedButton } from './Shared/Button';
import { Form } from './Shared/Form';
import { signIn } from '../api';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
  
    const handleSubmit = async (event) => {
      event.preventDefault();
      try {
        const response = await signIn({ username, password });
        alert('Logged in successfully!');
        console.log(response);
      } catch (error) {
        alert('Failed to log in');
      }
    };
  
    return (
      <Container>
        <Form
           initial={{ opacity: 0, y: 50 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.5 }}
        >
          <h1>Login</h1>
          <Input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <AnimatedButton onClick={handleSubmit}>Login</AnimatedButton>
        </Form>
      </Container>
    );
  };
  
  export default LoginPage;
