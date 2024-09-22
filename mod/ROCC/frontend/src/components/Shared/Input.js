import styled from '@emotion/styled';
import { motion } from 'framer-motion';

export const Input = styled(motion.input)`
  width: 100%;
  padding: 12px;
  margin: 12px 0;
  border: none;
  border-radius: 8px;
  background: #333;
  color: white;
  font-size: 16px;
  transition: background 0.3s;
  
  &:focus {
    background: #444;
    outline: none;
  }
`;
