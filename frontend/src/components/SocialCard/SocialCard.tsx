import "./SocialCard.css";

type SocialCardProps = {
  name: string;
  banner: string;
  onClick: () => void;
};

const SocialCard = ({ name, banner, onClick }: SocialCardProps) => {
  return (
    <div className="social-card" onClick={onClick}>
      <img src={banner} alt={name} className="card-banner" />
      <div className="card-overlay">
        <h2>{name}</h2>
      </div>
    </div>
  );
};

export default SocialCard;
