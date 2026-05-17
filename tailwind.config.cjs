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
          50: "#ffe5e5",
          100: "#ffcccc",
          500: "#EC0000",
          700: "#760000"
        }
      }
    }
  },
  plugins: []
};
