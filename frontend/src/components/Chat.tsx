import { useEffect, useState, useRef } from 'react';

import TextareaAutosize from "react-textarea-autosize";
import { FaArrowUp as SendIcon } from "react-icons/fa";

import './Chat.css'

type ChatProps = {
  user: {[key: string]: string};
};
type MessageContent = {
  type: string,
  text?: string,
  url?: string
}
type Message = {
  _id: string,
  user_id: string,
  role: string,
  content: [MessageContent],
  timestamp: string
}


const Chat = ({ user }: ChatProps) => {
  // States variables
  const [messages, setMessages] = useState<Message[]>([]);
  let lastMessage = useRef<string | null>(null);
  let waitingOnReply = useRef(false);
  let waitingOnMessages = useRef(false);
  let scrollLocked = useRef(true);
  let fullyLoaded = useRef(false);

  const messageAreaRef = useRef<HTMLDivElement>(null);

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
    if (area.scrollTop < 2 * area.clientHeight || area.scrollHeight <= area.clientHeight)
      getMessages();

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
    return input.trim() !== "";
  };
  useEffect(() => {
    if (waitingOnReply.current)
      return;
    setInputReady(validateInput());
  }, [input]);


  // Submit message to the API
  const sendMessage = async () => {
    waitingOnReply.current = true;
    setInputReady(false);

    // Post data
    const response = await fetch("/api/chat/send", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify([
        {"type": "text", "text": input}
      ])
    });
    if (response.status != 200) {
      alert("Bad connection");
      waitingOnReply.current = false;
      setInputReady(validateInput());
      return;
    }

    setInput("");

    // Add the result to the message pannel
    const body = await response.json();
    setMessages((previous) => {
      return [...previous, ...body]
    });
    if (lastMessage.current === null)
      lastMessage.current = body[body.length - 1]._id;

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
  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.shiftKey || e.key !== "Enter")
      return;
    e.preventDefault()
    if (inputReady) {
      sendMessage();
    }
  };

  // Visual
  return (
    <div id="pane">
      <div id="messages" ref={messageAreaRef}>
      {messages.length !== 0 ?
        messages.map((message, _index) =>
          message["role"] === "user" ? (
            <div key={message["_id"]} className="user">
              <p className="message--time">
                {getDisplay(message["timestamp"])}</p>
              <p className="message--content">{message["content"][0].text}</p>
            </div>
          ) : (
            <div key={message["_id"]} className="agent">
              <p className="message--time">
                Agent, {getDisplay(message["timestamp"])}</p>
              <p className="message--content">{message["content"][0].text}</p>
            </div>
          )
        ) : <p id="messages--empty">No messages, start your post!</p>
      }
      </div>
      <div id="input">
        <TextareaAutosize id="input--text" placeholder="Begin drafting..."
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey} maxRows={5}/>
        <button id="input--submit" onClick={sendMessage}
          disabled={!inputReady}><SendIcon /></button>
      </div>
    </div>
  )
}

export default Chat;
