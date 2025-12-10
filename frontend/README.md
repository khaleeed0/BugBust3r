# Security Scanner Frontend

React frontend application for the Security Scanner platform.

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on port 8000 (or configure `VITE_API_URL`)

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start development server
npm run dev
```

The application will be available at http://localhost:3000

### Build for Production

```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory (optional):

```env
# Backend API URL
VITE_API_URL=http://localhost:8000
```

**Note**: Environment variables must be prefixed with `VITE_` to be accessible in the application.

### Docker

When running in Docker, the API URL is automatically set to `http://backend:8000` via the Dockerfile.

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable React components
│   ├── contexts/       # React contexts (Auth)
│   ├── pages/          # Page components
│   ├── services/       # API service layer
│   ├── App.jsx         # Main app component
│   └── main.jsx        # Entry point
├── public/             # Static assets
├── package.json        # Dependencies
└── vite.config.js      # Vite configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Technologies

- **React 18** - UI library
- **React Router** - Client-side routing
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **React Toastify** - Toast notifications

## Troubleshooting

### Port Already in Use
If port 3000 is already in use, Vite will automatically try the next available port.

### CORS Errors
Ensure the backend CORS settings include your frontend URL. Check `backend/app/core/config.py`.

### API Connection Issues
- Verify the backend is running on port 8000
- Check `VITE_API_URL` environment variable
- Check browser console for detailed error messages

### Build Errors
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

