import { useEffect, useState } from "react";
import { HttpError } from "../api";

type Props = {
  error: HttpError | Error | null;
};

export default function ErrorBanner({ error }: Props) {
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    if (error instanceof HttpError && error.status === 429 && error.retryAfter) {
      setCountdown(error.retryAfter);
      const timer = setInterval(() => {
        setCountdown((c) => (c !== null && c > 0 ? c - 1 : 0));
      }, 1000);
      return () => clearInterval(timer);
    }
    setCountdown(null);
    return undefined;
  }, [error]);

  if (!error) return null;

  let message = error.message;
  if (error instanceof HttpError) {
    if (error.status === 429 && countdown !== null) {
      message = `${error.message} (${countdown}s remaining)`;
    } else if (error.status >= 500) {
      const detail = error.message?.trim();
      message =
        detail && detail.length < 220
          ? detail
          : "The service is temporarily unavailable. Please try again shortly.";
    }
  } else {
    message =
      "Network error. Check that the API is running (Docker: port 8001 by default, or see README).";
  }

  return (
    <div className="error-banner" role="alert">
      {message}
    </div>
  );
}
