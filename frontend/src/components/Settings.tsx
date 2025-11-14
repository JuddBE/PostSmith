// import { useEffect, useState, useRef } from 'react';
import React from "react";
import {
  Modal, Box, Typography, IconButton, Button
} from "@mui/material";
import CloseIcon from '@mui/icons-material/Close';
import LogOutIcon from '@mui/icons-material/DoorBackOutlined';
import DeleteIcon from '@mui/icons-material/DeleteForeverOutlined';

import "./Settings.css"


type SettingsProps = {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  user: {[key: string]: string};
  setUser: React.Dispatch<React.SetStateAction<{[key: string]: string} | null>>;
};

const Settings = ({ open, setOpen, user, setUser }: SettingsProps) => {
  const close = () => setOpen(false);
  const x_login = () => {
    window.location.href="/api/oauth/x/login";
  };
  const x_unlink = async () => {
    await fetch("/api/oauth/x/unlink", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
      },
    });
    setUser(prev => {
      const { x_username, ...rest } = prev!;
      return rest;
    });
  };
  const reddit_login = () => {
    window.location.href="/api/oauth/reddit/login";
  };
  const reddit_unlink = async () => {
    await fetch("/api/oauth/reddit/unlink", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
      },
    });
    setUser(prev => {
      const { r_username, ...rest } = prev!;
      return rest;
    });
  };
  const deleteMessages = async () => {
    if (!window.confirm("Are you sure you want to clear your messages?"))
      return;
    await fetch("/api/chat/clear", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
      },
    });
    window.location.reload();
  };
  const logout = () => {
    if (!window.confirm("Are you sure you want to logout?"))
      return;
    localStorage.removeItem("token");
    window.location.reload();
  };

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
      p: 6,
      display: "flex",
      flexDirection: "column",
      gap: 2
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

    <Typography component="h4" gutterBottom>Linked APIS</Typography>
    {
      !user.x_username ? (
        <Button
          variant="contained"
          color="primary"
          onClick={x_login}
          >Link Twitter</Button>
      ) : (
        <Button
          variant="contained"
          color="warning"
          onClick={x_unlink}
          >Unlink Twitter</Button>
      )
    }
    {
      !user.r_username ? (
        <Button
          variant="contained"
          color="primary"
          onClick={reddit_login}
          >Link Reddit</Button>
      ) : (
        <Button
          variant="contained"
          color="warning"
          onClick={reddit_unlink}
          >Unlink Reddit</Button>
      )
    }

    <Typography component="h4" gutterBottom>Account Controls</Typography>
    <Button
      variant="contained"
      color="error"
      startIcon={<DeleteIcon />}
      onClick={deleteMessages}
      >Delete all Messages.</Button>
    <Button
      variant="contained"
      color="error"
      startIcon={<LogOutIcon />}
      onClick={logout}
      >Log out.</Button>

    </Box>
  </Modal>);
};

export default Settings;
