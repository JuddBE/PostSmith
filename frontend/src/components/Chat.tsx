import './Chat.css'

type ChatProps = {
  user: {[key: string]: string}
};
const Chat = ({ user }: ChatProps) => {

  return (
    <>
      <p>Hello, {user.email}.</p>
      <input type="text" />
    </>
  )
}

export default Chat;
