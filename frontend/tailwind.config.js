/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cream: "#F7F3EC",
        panel: "#FFFFFF",
        ink: "#221F1B",
        charcoal: "#1E1B18",
        muted: "#847C6E",
        line: "#E4DCD0",
        blush: "#F1D8D6",
        sage: "#93A98D",
        sagelight: "#E1E9DC"
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
        script: ["var(--font-script)", "cursive"]
      }
    }
  },
  plugins: []
};
