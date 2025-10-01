# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh 
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

## Using the Flask backend during development

This frontend is configured to forward any requests under `/api` to a backend server using Vite's dev server proxy. By default the proxy target is `http://localhost:42057` which matches the Flask backend used in this project.

You can override the target or use a full API URL in production with environment variables:

- `VITE_API_TARGET` — used by Vite dev server to proxy `/api` to your backend (default: `http://localhost:42057`).
- `VITE_API_URL` — used by the frontend code as the base URL for API requests. If not set it defaults to the relative path `/api` so the dev proxy is used.

To run the frontend and have it proxy to the Flask backend, make sure your Flask app is running (default port 42057 in this repo), then run:

```powershell
npm install
npm run dev
```

If your Flask backend listens on a different host/port, create a `.env` file at the project root or set `VITE_API_TARGET` in your environment. Example `.env`:

```
VITE_API_TARGET=http://10.15.3.30:42057
# Optionally set VITE_API_URL for production builds
VITE_API_URL=http://10.15.3.30:42057/api
```

When building for production you may want to set `VITE_API_URL` to the absolute backend URL so the built app calls the backend directly instead of relying on a proxy.

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
