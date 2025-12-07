# Voice Collection Platform - Frontend

This is the React frontend for the Voice Data Collection Platform, built to crowdsource Bangla voice recordings and transcriptions for training Sworik AI.

## Features

- **Authentication System**: JWT-based authentication with role-based access control
- **Responsive Design**: Built with Tailwind CSS for mobile and desktop
- **Protected Routes**: Role-based route protection for different user types
- **Audio Components**: Reusable audio player and recorder components
- **User Management**: Context-based user state management

## Tech Stack

- **React 19** with TypeScript
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Headless UI** for accessible components
- **Heroicons** for icons
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running on port 8000

### Installation

1. Install dependencies:

```bash
npm install
```

2. Copy environment file:

```bash
cp .env.example .env
```

3. Update the API URL in `.env` if needed:

```
REACT_APP_API_URL=http://localhost:8000/api
```

### Development

Start the development server:

```bash
npm start
```

The app will be available at http://localhost:3000

### Building

Create a production build:

```bash
npm run build
```

## Project Structure

```
src/
├── components/
│   ├── auth/           # Authentication components
│   ├── audio/          # Audio player and recorder
│   ├── common/         # Reusable UI components
│   └── layout/         # Layout and navigation
├── contexts/           # React contexts
├── pages/              # Page components
├── services/           # API services
└── types/              # TypeScript type definitions
```

## User Roles

- **contributor**: Can record voice and transcribe audio
- **admin**: Can access admin dashboard and manage platform
- **sworik_developer**: Can export data and access all features

## Components

### Authentication

- `AuthProvider`: Context provider for authentication state
- `ProtectedRoute`: Route wrapper for authenticated access
- `LoginForm`: User login interface

### Audio

- `AudioPlayer`: Playback controls with waveform visualization
- `AudioRecorder`: Voice recording with real-time feedback

### Layout

- `Layout`: Main application layout with navigation
- `Navbar`: Responsive navigation with user menu

## API Integration

The frontend communicates with the FastAPI backend through:

- JWT token authentication
- Automatic token refresh
- Error handling and user feedback
- Role-based API access

## Next Steps

This foundation supports the implementation of:

- Voice recording interface (Task 12)
- Transcription interface (Task 13)
- Admin dashboard (Task 14)
- Data export interface (Task 15)
