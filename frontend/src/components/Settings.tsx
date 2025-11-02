// import { useEffect, useState, useRef } from 'react';
import React from "react";
import {
  Modal, Box, Typography, IconButton
} from "@mui/material";
import CloseIcon from '@mui/icons-material/Close';

import "./Settings.css"


type SettingsProps = {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  user: {[key: string]: string};
};

const Settings = ({ open, setOpen, user }: SettingsProps) => {
  const close = () => setOpen(false);

  return (<Modal open={open} onClose={close} aria-labelledby="modal--title">
    <Box sx={{
      position: "absolute" as "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      width: 400,
      maxHeight: "50%",
      overflowY: "auto",
      bgcolor: "#2a2b45",
      borderRadius: 2,
      boxShadow: 24,
      p: 4
    }}>
    <IconButton sx={{
        position: "absolute" as "absolute",
        top: "5px",
        right: "5px",
        padding: "6px",
        backgroundColor: "rgba(255,255,255,0.1)"
        }} onClick={close}>
      <CloseIcon /></IconButton>
    <Typography id="modal--title" component="h2" gutterBottom>
      Settings</Typography>

    Hello, {user.email}

    </Box>
  </Modal>);
};

export default Settings;
