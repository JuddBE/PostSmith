import "./Header.css";

type HeaderProps = {
  username: string;
};

const Header = ({ username }: HeaderProps) => {
  return (
    <header className="dashboard-header">
      <h1>PostSmith Dashboard</h1>
      <div className="user-info">
        <span>{username}</span>
        <img
          src="https://cdn-icons-png.flaticon.com/512/1077/1077114.png"
          alt="User avatar"
          className="user-avatar"
        />
      </div>
    </header>
  );
};

export default Header;
