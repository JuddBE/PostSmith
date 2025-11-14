import { useEffect, useState, useRef } from 'react';

import {
  IconButton,
  InputAdornment,
  TextField
} from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import ImageIcon from "@mui/icons-material/Image";
import SendIcon from "@mui/icons-material/Send";

import Settings from "./Settings";

import "./Chat.css";


/*
 * Definitions
 * */
type ChatProps = {
  user: {[key: string]: string};
};
type Message = {
  _id: string,
  user_id: string,
  role: string,
  content_type: string,
  content: string,
  imageuri?: string
  timestamp: string
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
const Chat = ({ user }: ChatProps) => {
  // States variables
  const [messages, setMessages] = useState<Message[]>([]);
  const [image, setImage] = useState<Image | undefined>(undefined);
  const [open, setOpen] = useState<boolean>(false);
  const [status, setStatus] = useState("");
  const lastMessage = useRef<string | null>(null);
  const waitingOnReply = useRef(false);
  const waitingOnMessages = useRef(false);
  const scrollLocked = useRef(true);
  const fullyLoaded = useRef(false);


  const messageAreaRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const [input, setInput] = useState("");
  const [inputReady, setInputReady] = useState(true);

  // Get recent messages
  const getMessages = async () => {
    if (fullyLoaded.current || waitingOnMessages.current)
      return;
    waitingOnMessages.current = true;

    const options = lastMessage.current ? "?start=" + lastMessage.current : "";
    const response = await fetch("/api/chat/messages" + options, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
      }
    });
    const body = await response.json();

    if (response.status == 200) {
      if (body.length !== 0) {
        lastMessage.current = body[body.length - 1]._id;
        setMessages((previous) => {
          return [...body, ...previous]
        });
      } else {
        fullyLoaded.current = true;
      }
    } else {
      alert("Bad connection");
    }
    waitingOnMessages.current = false;
  };
  useEffect(() => {
    getMessages();
  }, []);


  // Scroll lock, auto load
  const onScroll = () => {
    const area = messageAreaRef.current;
    if (area === null)
      return;

    // If near top, load more
    //if (area.scrollTop < 2 * area.clientHeight || area.scrollHeight <= area.clientHeight)
      //getMessages();

    // If near bottom, follow it
    const bottom = area.scrollHeight - area.clientHeight;
    scrollLocked.current = bottom - area.scrollTop < .3 * area.clientHeight;
  };

  // Bind on scroll
  useEffect(() => {
    const area = messageAreaRef.current;
    if (area === null)
      return;

    // Initial check
    onScroll();

    // Handle listener
    area.addEventListener("scroll", onScroll);
    return () => area.removeEventListener("scroll", onScroll);
  }, []);


  // Scroll to bottom if locked
  useEffect(() => {
    const area = messageAreaRef.current;
    if (area === null || !scrollLocked.current)
      return;
    area.scrollTop = area.scrollHeight - area.clientHeight;
  }, [messages, input]);


  // Disable button when there is no text
  const validateInput = () => {
    return input.trim() !== "" || (image !== undefined && !image.loading);
  };
  useEffect(() => {
    if (waitingOnReply.current || (!image || !image.loading))
      return;
    setInputReady(validateInput());
  }, [waitingOnReply.current, input, image, image?.loading]);


  // Submit message to the API
  const sendMessage = async () => {
    if (image && image.loading) {
      alert("Input image still loading...");
      return;
    }

    waitingOnReply.current = true;
    setInputReady(false);

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
      alert("Bad connection");
      waitingOnReply.current = false;
      setInputReady(validateInput());
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


    /*const body = await response.json();
    setMessages((previous) => {
      return [...previous, ...body]
    });
    if (lastMessage.current === null)
      lastMessage.current = body[body.length - 1]._id;*/

    waitingOnReply.current = false;
    setInputReady(validateInput());
  };

  // Get local time display from UTC string
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
    if (inputReady) {
      sendMessage();
    }
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
    <Settings open={open} setOpen={setOpen} user={user} />

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
              <p className="message--status" style={{ whiteSpace: "pre-line" }}>
                {status}
              </p>
            </div>
          )}
        </>
      ) : waitingOnMessages.current ? (
        <p id="messages--empty">Loading history...</p>
      ) : (
        <p id="messages--empty">No messages yet, start your draft!</p>
      )}
      </div>

      {/*
        * User image input displays
        */}
      <div id="inputimage">
        {
          image ? (
            !image.loading ? (
              <img src={image.url} />
            ) : (
              <div className="loadingimg" />
            )
          ) : null
        }
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
            <IconButton onClick={callAddImage}>
              <ImageIcon />
            </IconButton>
          </InputAdornment>),
          endAdornment: (<InputAdornment position="start">
            <IconButton onClick={sendMessage}>
              <SendIcon />
            </IconButton>
          </InputAdornment>)
        }}
      />
    </div>
  </>
  )
};

export default Chat;
