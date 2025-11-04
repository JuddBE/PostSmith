import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

type XProps = {
  user: {[key: string]: string};
};
const X = ({ user }: XProps) => {
  const [params] = useSearchParams();
  const access_token = params.get("access_token");
  const refresh_token = params.get("refresh_token");
  const expires_at = params.get("expires_at");
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
          "access_token": access_token,
          "refresh_token": refresh_token,
          "expires_at": expires_at,
          "username": username
        })
      });

      window.location.href = "/";
    };

    if (access_token)
      upload();
  }, [access_token]);

  return (<h1>Loading...</h1>);
};

export default X;
