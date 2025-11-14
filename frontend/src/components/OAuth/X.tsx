import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

type XProps = {
  user: {[key: string]: string};
};
const X = ({ user }: XProps) => {
  const [params] = useSearchParams();
  const token = params.get("token");
  const token_secret = params.get("token_secret");
  const username = params.get("username");

  useEffect(() => {
    const upload = async () => {
      await fetch("/api/oauth/x/save", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${user["token"]}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "token": token,
          "token_secret": token_secret,
          "username": username,
        })
      });

      window.location.href = "/";
    };

    if (token && token_secret && username)
      upload();
  }, [token, token_secret, username]);

  return (<h2>Linking account...</h2>);
};

export default X;
