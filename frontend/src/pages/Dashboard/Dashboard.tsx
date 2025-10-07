import { useNavigate } from "react-router-dom";
import Header from "../../components/Header/Header";
import SocialCard from "../../components/SocialCard/SocialCard";
import "./Dashboard.css";

import twitterBanner from "../../assets/twitter-banner.webp";
import redditBanner from "../../assets/reddit-banner.jpg";
import blueskyBanner from "../../assets/bluesky-banner.jpeg";
import youtubeBanner from "../../assets/youtube-banner.png";

type DashboardProps = {
  user: { [key: string]: string };
};

const Dashboard = ({ user }: DashboardProps) => {
  const navigate = useNavigate();

  const platforms = [
    { name: "Twitter / X", route: "/dashboard/twitter", banner: twitterBanner },
    { name: "Reddit", route: "/dashboard/reddit", banner: redditBanner },
    { name: "Bluesky", route: "/dashboard/bluesky", banner: blueskyBanner },
    { name: "YouTube", route: "/dashboard/youtube", banner: youtubeBanner }
  ];

  return (
    <div className="dashboard">
      <Header username={user.email || user.name || "User"} />
      <div className="card-grid">
        {platforms.map((p) => (
          <SocialCard
            key={p.name}
            name={p.name}
            banner={p.banner}
            onClick={() => navigate(p.route)}
          />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
