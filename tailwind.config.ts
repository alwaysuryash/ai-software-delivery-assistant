import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
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
