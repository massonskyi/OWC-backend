import React, {useState} from 'react';
import { Container } from './Shared/Container';
import { Input } from './Shared/Input';
import { AnimatedButton } from './Shared/Button';
import { Form } from './Shared/Form';
import { signUp } from '../api';

const RegisterPage = () => {
    const [name, setName] = useState('');
    const [surname, setSurname] = useState('');
    const [age, setAge] = useState('');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('');
    const [avatar, setAvatar] = useState('');
  
    const handleSubmit = async (event) => {
      event.preventDefault();
      try {
        const response = await signUp({ name, surname, age: parseInt(age, 10), username, email, password, role, avatar });
        alert('Registered successfully!');
        console.log(response);
      } catch (error) {
        alert('Failed to register');
      }
    };
  
    return (
      <Container>
        <Form
           initial={{ opacity: 0, y: 50 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.5 }}
        >
          <h1>Register</h1>
          <Input type="text" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <Input type="text" placeholder="Surname" value={surname} onChange={(e) => setSurname(e.target.value)} />
          <Input type="number" placeholder="Age" value={age} onChange={(e) => setAge(e.target.value)} />
          <Input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Input type="text" placeholder="Role" value={role} onChange={(e) => setRole(e.target.value)} />
          <Input type="text" placeholder="Avatar URL" value={avatar} onChange={(e) => setAvatar(e.target.value)} />
          <AnimatedButton onClick={handleSubmit}>Register</AnimatedButton>
        </Form>
      </Container>
    );
  };
  
  export default RegisterPage;
