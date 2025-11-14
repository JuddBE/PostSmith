import { useEffect, useState, useRef } from 'react';

import {
  IconButton,
  InputAdornment,
  TextField
} from "@mui/material";
import CloseIcon from '@mui/icons-material/Close';
import ImageIcon from "@mui/icons-material/Image";
import SendIcon from "@mui/icons-material/Send";
import SettingsIcon from "@mui/icons-material/Settings";

import { DotLoader, PropagateLoader, PulseLoader } from "react-spinners";

import Settings from "./Settings";
import "./Chat.css";


/*
 * Definitions
 * */
type ChatProps = {
  user: {[key: string]: string};
  setUser: React.Dispatch<React.SetStateAction<{[key: string]: string} | null>>;
};
type Message = {
  _id: string;
  user_id: string;
  role: string;
  content_type: string;
  content: string;
  imageuri?: string;
  timestamp: string;
};

type Image = {
  loading: boolean;
  id: string;
  file: File;
  url?: string;
};


/*
 * Behavior
 * */
const Chat = ({ user, setUser }: ChatProps) => {
  // States variables
  const [open, setOpen] = useState<boolean>(false);

  // Waiting states
  const [pendingMessages, setPendingMessages] = useState(true);
  const [pendingReply, setPendingReply] = useState(false);

  // Scrolling state
  const scrollLocked = useRef(true);

  // Messages state
  const [status, setStatus] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const messageAreaRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Input state
  const [image, setImage] = useState<Image | undefined>(undefined);
  const [input, setInput] = useState("");

  // Pull message history
  const getMessages = async () => {
    setPendingMessages(true)

    const response = await fetch("/api/chat/messages", {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
      }
    });
    const body = await response.json();

    if (response.status == 200) {
      if (body.length !== 0) {
        setMessages((previous) => {
          return [...body, ...previous]
        });
      }
    } else {
      alert("Bad connection");
    }
    setPendingMessages(false)
  };
  useEffect(() => {
    getMessages();
  }, []);


  // Bind scroll listener
  useEffect(() => {
    const area = messageAreaRef.current;
    if (area === null)
      return;

    // Initial check
    onScroll();

    // Handle listener
    area.addEventListener("scroll", onScroll);
    return () => area?.removeEventListener("scroll", onScroll);
  }, [messageAreaRef.current]);
  // Scroll lock, auto scroll down on messages
  const onScroll = () => {
    const area = messageAreaRef.current;
    if (area === null)
      return;

    // If near bottom, follow it
    const bottom = area.scrollHeight - area.clientHeight;
    scrollLocked.current = bottom - area.scrollTop < .3 * area.clientHeight;
  };
  // If locked, scroll to bottom on: message, status, or input
  useEffect(() => {
    const area = messageAreaRef.current;
    if (area === null || !scrollLocked.current)
      return;
    area.scrollTop = area.scrollHeight - area.clientHeight;
  }, [messages, status, input]);


  // Check if the user should be able to submit input
  const inputReady = () => {
    const hasInput =
      (input.trim() !== "" && (image === undefined || !image.loading))
      || (image && !image.loading);
    return hasInput && !pendingReply;
  };


  // Submit message to the API
  const sendMessage = async () => {
    // Validate state
    if (image && image.loading) {
      alert("Input image still loading...");
      return;
    } else if ((!input.trim() && !image) || pendingReply) {
      return;
    }
    setPendingReply(true);

    // Save and clear fields immediately
    const input_text = input;
    const input_image = image;
    setInput("");
    setImage(undefined);

    // Post data
    const response = await fetch("/api/chat/send", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "text": input_text,
        "imageuri": input_image?.url
      })
    });
    if (response.status != 200 || !response.body) {
      alert("Internal server error");
      setPendingReply(false);
      return;
    }

    // Stream body
    const decoder = new TextDecoder()
    const reader = response.body.getReader();

    let buffer = "";
    while (true) {
      // Get available data
      const { done, value } = await reader.read();
      if (done) {
        setStatus("");
        break;
      }
      buffer += decoder.decode(value, { stream: true });

      // Set messages
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""
      for (const line of lines) {
        if (!line)
          continue;
        const content = JSON.parse(line);
        if ("status" in content) {
          setStatus(content["message"]);
        } else {
          setMessages((previous) => {
            return [...previous, content]
          });
        }
      }
    }

    // Finished, ready for next message
    setPendingReply(false);
  };

  // Get readable time display from UTC string
  const getDisplay = (utc: string) => {
    return (new Date(utc)).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  }

  // On enter, submit text
  const handleKey = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.shiftKey || e.key !== "Enter")
      return;
    e.preventDefault()
    sendMessage();
  };

  const addImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    if (files.length == 0)
      return;
    const file = files[0]

    const id = crypto.randomUUID();
    setImage({loading: true, id, file});

    const reader = new FileReader();
    reader.onload = () => {
      setImage(prev => prev?.id === id
        ? {...prev, url: reader.result as string, loading: false}
        : prev);
    };
    reader.readAsDataURL(file);
  };
  const callAddImage = (_e: React.MouseEvent<HTMLButtonElement>) => {
    fileRef.current?.click();
  };

  const openSettings = () => {
    setOpen(true);
  };

  // Visual
  return (
  <>
    {/* Settings menu components */}
    <IconButton
      sx={{
        position: "fixed", top: 12, right: 12,
        padding: "12px",
        backgroundColor: "rgba(255,255,255,0.1)",
        color: "lightgray"
      }}
      onClick={openSettings}
      ><SettingsIcon />
    </IconButton>
    <Settings open={open} setOpen={setOpen} user={user} setUser={setUser} />

    {/* Center pane */}
    <div id="pane">
      {/*
        * Message display
        * */}
      <div id="messages" ref={messageAreaRef}>
      {messages.length !== 0 || status ? (
        <>
          {messages.map((message, _index) => (
            <div key={message["_id"]} className={message.role === "user" ? "user" : "agent"}>
              <p className="message--time">
                {getDisplay(message["timestamp"])}
              </p>

              <p className="message--content" style={{ whiteSpace: "pre-line" }}>
                {message["content_type"] === "text" ? (
                  message["content"]
                ) : (
                  <img src={message["imageuri"]!} />
                )}
              </p>
            </div>
          ))}

          {status && (
            <div className={"agent"}>
              <p className="message--status"
                  style={{ whiteSpace: "pre-line", width: "40%",
                    display: "flex", flexDirection: "column",
                    alignItems: "center", gap: "8px" }}>
                {status}
                <PulseLoader color="gray" size={10} />
              </p>
            </div>
          )}
        </>
      ) : pendingMessages ? (
        <p id="messages--empty"><PropagateLoader  color="#1a1a2b"/></p>
      ) : (
        <p id="messages--empty">No messages yet, start your draft!</p>
      )}
      </div>

      {/*
        * User image input displays
        */}
      <div id="inputimage">
        { image && (
            !image.loading ? (
              <>
                <img src={image.url} />
                <IconButton
                  sx={{
                    padding: "8px",
                    backgroundColor: "rgba(255,255,255,0.1)",
                    color: "gray"
                  }}
                  onClick={() => setImage(undefined)}
                  ><CloseIcon />
                </IconButton>
              </>
            ) : (
              <div className="loadingimg" />
            )
        )}
      </div>


      {/*
        * User input fields and buttons
        */}
      <input type="file" id="input--file" accept="image/*"
        ref={fileRef} onChange={addImage} />
      <TextField
        value={input} onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKey}
        multiline
        maxRows={5}
        placeholder="Begin drafting..."
        sx={{
          margin: "10px 10% 10px 10%",
          "& .MuiOutlinedInput-root": {
            borderRadius: "12px",
            backgroundColor: "#474862",
          },
          "& .MuiOutlinedInput-input": {
            fontSize: "20px",
            color: "#010101"
          },
          "& .MuiInputAdornment-root .MuiIconButton-root": {
            padding: "8px",
            backgroundColor: "rgba(255,255,255,0.1)"
          }
        }}

        InputProps={{
          startAdornment: (<InputAdornment position="start">
            <IconButton onClick={callAddImage} sx={{width:40, height:40, padding:0}}>
              <ImageIcon />
            </IconButton>
          </InputAdornment>),
          endAdornment: !pendingReply ? (
            <InputAdornment position="start">
              <IconButton onClick={sendMessage} disabled={!inputReady()} sx={{width:40, height:40, padding:0}}>
                <SendIcon />
              </IconButton>
            </InputAdornment>
          ) : (
            <InputAdornment position="start">
              <IconButton disabled sx={{width:40, height:40, padding:0}}>
                <DotLoader color="#333" size={20} />
              </IconButton>
            </InputAdornment>
          )
        }}
      />
    </div>
  </>
  )
};

export default Chat;
