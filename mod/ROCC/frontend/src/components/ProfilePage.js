import React, { useState } from 'react';
import { motion } from 'framer-motion';

const ProfilePage = () => {
  const [name, setName] = useState("John Doe");
  const [email, setEmail] = useState("johndoe@example.com");
  const [profilePicture, setProfilePicture] = useState("https://via.placeholder.com/150");

  const handleNameChange = (e) => setName(e.target.value);
  const handleEmailChange = (e) => setEmail(e.target.value);
  const handleProfilePictureChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setProfilePicture(URL.createObjectURL(file));
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center space-y-6">
      <motion.div 
        className="p-6 bg-secondary rounded-xl shadow-lg"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex flex-col items-center space-y-4">
          <motion.img
            src={profilePicture}
            alt="Profile"
            className="w-32 h-32 rounded-full shadow-lg"
            whileHover={{ scale: 1.1 }}
          />
          <input
            type="file"
            accept="image/*"
            className="hidden"
            id="profile-picture-upload"
            onChange={handleProfilePictureChange}
          />
          <label
            htmlFor="profile-picture-upload"
            className="text-accent cursor-pointer"
          >
            Change Picture
          </label>
          <motion.input
            type="text"
            value={name}
            onChange={handleNameChange}
            className="bg-transparent text-center text-2xl font-semibold text-white outline-none"
            whileFocus={{ borderColor: '#00FFFF' }}
          />
          <motion.input
            type="email"
            value={email}
            onChange={handleEmailChange}
            className="bg-transparent text-center text-lg text-gray-300 outline-none"
            whileFocus={{ borderColor: '#00FFFF' }}
          />
          <motion.button
            className="mt-4 px-6 py-2 bg-accent text-primary rounded-full shadow-lg"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Save Changes
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
};

export default ProfilePage;
