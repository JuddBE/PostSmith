// import { useEffect, useState, useRef } from 'react';
import React from "react";
import { useState } from "react";
import {
  Dialog, DialogTitle, DialogContent, IconButton, Typography, Button, Box, TextField
} from "@mui/material";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useTheme } from "@mui/material/styles";
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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [blueskyOpen, setBlueskyOpen] = useState(false);
  const [bkHandle, setBkHandle] = useState("");
  const [bkPassword, setBkPassword] = useState("");
  const [bkSending, setBkSending] = useState(false);

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
  const bluesky_save = async() => {
    if (!bkHandle || !bkPassword) {
      alert("Please enter your Bluesky handle and app password.");
      return;
    }

    setBkSending(true);
    await fetch("/api/bk/save", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "username": bkHandle,
        "password": bkPassword
      })
    });

    setUser((prev) => ({
      ...prev,
      bk_username: bkHandle
    }));

    setBkSending(false);
  };
  const bluesky_unlink = async () => {
    await fetch("/api/oauth/bk/unlink", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
      },
    });
    setUser(prev => {
      const { bk_username, ...rest } = prev!;
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

  return (
    <Dialog open={open} onClose={close} fullScreen={isMobile}
        PaperProps={{
          sx: {
            bgcolor: "#2a2b45", borderRadius: isMobile ? 0 : 2, p: 4, color: "#fff"
          }
        }}>
      <DialogTitle sx={{
            position: "relative", pb: 1, display: "flex", alignItems: "center",
            flexDirection: "row", justifyContent: "space-between"
          }}>
        Settings
        <IconButton edge="end" sx={{backgroundColor: "rgba(255,255,255,0.1)"}}
            onClick={close}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{
            display: "flex", flexDirection: "column", gap: 2,
            minWidth: 350, "@media (max-width: 620px)": {
              minWidth: "100%",
              padding: "0"
            }
          }}>
        <Typography component="h4" gutterBottom>Linked APIS</Typography>
        {
          !user.x_username ? (
            <Button variant="contained" color="primary" onClick={x_login}
              >Link Twitter</Button>
          ) : (
            <Button variant="contained" color="warning" onClick={x_unlink}
              >Unlink Twitter</Button>
          )
        }
        {
          !user.r_username ? (
            <Button variant="contained" color="primary" onClick={reddit_login}
              >Link Reddit</Button>
          ) : (
            <Button variant="contained" color="warning" onClick={reddit_unlink}
              >Unlink Reddit</Button>
          )
        }
        {
          !user.bk_username ? (
            blueskyOpen ? (
              <Box display="flex" flexDirection="column" gap={1} sx={{ border: "1px solid #888", borderRadius: 1, p: 2 }}>
                <Typography variant="subtitle1">Bluesky</Typography>
                <TextField color="primary" label="Handle"
                    value={bkHandle} onChange={(e) => setBkHandle(e.target.value)}
                    sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#bbb',
                      '& fieldset': { borderColor: '#bbb' },
                      '&:hover fieldset': { borderColor: '#999' }
                    },
                    '& .MuiInputLabel-root': {
                      color: '#bbb',
                    }
                  }}/>
                <TextField color="primary" label="App Password" type="password"
                    value={bkPassword} onChange={(e) => setBkPassword(e.target.value)}
                    sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#bbb',
                      '& fieldset': { borderColor: '#bbb' },
                      '&:hover fieldset': { borderColor: '#999' }
                    },
                    '& .MuiInputLabel-root': {
                      color: '#bbb',
                    }
                  }}/>
                <Box display="flex" flexDirection="row" gap={1} width="100%">
                  <Button variant="contained" color="warning" sx={{ flex: 1 }}
                    onClick={() => setBlueskyOpen(false)}>
                      Cancel
                  </Button>
                  <Button variant="contained" color="primary" sx={{ flex: 1 }}
                    onClick={bluesky_save} loading={bkSending}>
                      Save
                  </Button>
                </Box>
              </Box>
            ) : (
              <Button variant="contained" color="primary" onClick={() => setBlueskyOpen(true)}
                >Link Bluesky</Button>
            )
          ) : (
            <Button variant="contained" color="warning" onClick={bluesky_unlink}
              >Unlink Bluesky</Button>
          )
        }

        <Typography component="h4" sx={{ mt: 2 }}>Account Controls</Typography>
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
      </DialogContent>
    </Dialog>
  );
};

export default Settings;
