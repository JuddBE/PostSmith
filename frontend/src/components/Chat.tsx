import { useEffect, useState, useRef } from 'react';

import TextareaAutosize from "react-textarea-autosize";
import {
  FaArrowUp as SendIcon, FaImage as AddIcon
} from "react-icons/fa";

import './Chat.css'

type ChatProps = {
  user: {[key: string]: string};
};
type MessageContent = {
  type: string,
  text?: string,
  image_url?: string
};
type Message = {
  _id: string,
  user_id: string,
  role: string,
  content: [MessageContent],
  timestamp: string
};

type Image = {
  loading: boolean;
  id: string;
  file: File;
  url?: string;
};


const Chat = ({ user }: ChatProps) => {
  // States variables
  const [messages, setMessages] = useState<Message[]>([]);
  const [images, setImages] = useState<Image[]>([]);
  const [loadingImages, setLoadingImages] = useState<number>(0);
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
    if (waitingOnReply.current || loadingImages !== 0)
      return;
    setInputReady(validateInput());
  }, [input, loadingImages]);


  // Submit message to the API
  const sendMessage = async () => {
    let ready = true;
    images.forEach(image => {
      if (image.loading || !image.url) {
        ready = false;
      }
    });
    if (!ready) {
      alert("Input images still loading...");
      return;
    }

    waitingOnReply.current = true;
    setInputReady(false);

    const message: MessageContent[] = [
      {"type": "input_text", "text": input}
    ]

    images.forEach(image => message.push({
      "type": "input_image", "image_url": image.url! 
    }));


    // Post data
    const response = await fetch("/api/chat/send", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${user["token"]}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(message)
    });
    if (response.status != 200) {
      alert("Bad connection");
      waitingOnReply.current = false;
      setInputReady(validateInput());
      return;
    }

    setInput("");
    setImages([]);

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

  const addImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    const images: Image[] = files.map(file => ({
      loading: true,
      id: crypto.randomUUID(),
      file
    }));
    setImages(prev => [...prev, ...images]);
    setLoadingImages(prev => prev + images.length);
    images.forEach(image => {
      const reader = new FileReader();
      reader.onload = () => {
        setImages(prev => prev.map(
          itr => itr.id === image.id ? {
            ...itr,
            url: reader.result as string,
            loading: false
          } : itr
        ));
        setLoadingImages(prev => prev - 1);
      };
      reader.readAsDataURL(image.file);
    });
  };
  const callAddImage = (_e: React.MouseEvent<HTMLButtonElement>) => {
    fileRef.current?.click();
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
              <p className="message--content">
              <div className="images">
                {message["content"].slice(1).map((image, index) =>
                    <img key={index} src={image.image_url} className="image" />
                )}
              </div>
              {message["content"][0].text}
              </p>
            </div>
          ) : (
            <div key={message["_id"]} className="agent">
              <p className="message--time">
                Agent, {getDisplay(message["timestamp"])}</p>
              <div className="images">
                {message["content"].slice(1).map((image, index) =>
                    <img key={index} src={image.image_url} className="image" />
                )}
              </div>
              <p className="message--content">{message["content"][0].text}</p>
            </div>
          )
        ) : <p id="messages--empty">No messages, start your post!</p>
      }
      </div>
      <div className="images">
      {images.map((image, index) =>
        !image.loading ? (
          <img key={index} src={image.url} className="image" />
        ) : (
          <div key={index} className="image--loading" />
        )
      )}
      </div>
      <div id="input">
        <input type="file" id="input--file" accept="image/*"
          ref={fileRef} onChange={addImage} />
        <button id="input--add" onClick={callAddImage}>
          <AddIcon /></button>
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
