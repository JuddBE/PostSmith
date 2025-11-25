import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { PropagateLoader } from "react-spinners";

type RedditProps = {
  user: {[key: string]: string};
};
const Reddit = ({ user }: RedditProps) => {
  const [params] = useSearchParams();
  const refresh_token = params.get("refresh_token");
  const username = params.get("username");

  useEffect(() => {
    const upload = async () => {
      await fetch("/api/oauth/reddit/save", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${user["token"]}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "refresh_token": refresh_token,
          "username": username
        })
      });

      window.location.href = "/";
    };

    if (refresh_token)
      upload();
  }, [refresh_token]);

  return (<PropagateLoader color="#2a2b45" />);
};

export default Reddit;
