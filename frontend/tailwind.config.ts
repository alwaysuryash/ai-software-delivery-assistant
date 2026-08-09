import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}", "./src/app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontSize: {
        "2xs": "0.625rem",
        "3xs": "0.5rem",
      },
      colors: {
        health: {
          green: "#15803d",
          amber: "#b45309",
          red: "#b91c1c",
          unknown: "#6b7280",
        },
      },
    },
  },
  plugins: [],
};

export default config;
