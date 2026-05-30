export const env = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME ?? "ACIP",
  NEXT_PUBLIC_ENV: process.env.NODE_ENV ?? "development",
};

export const isDev = env.NEXT_PUBLIC_ENV === "development";
export const isProd = env.NEXT_PUBLIC_ENV === "production";
