module.exports = {
  content: [
    "./app/presentation/web/templates/**/*.html",
    "./app/presentation/**/*.py",
    "./tests/**/*.py"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff7f0",
          100: "#d9ebdc",
          500: "#2f6b3c",
          700: "#224f2d"
        }
      }
    }
  },
  plugins: []
};
