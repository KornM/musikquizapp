# Music Quiz Frontend

Vue.js 3 + Vuetify 3 frontend for the Music Quiz application.

## Features

- **Admin Interface**
  - Secure login with JWT authentication
  - Dashboard with session management
  - Create quiz sessions with rounds
  - Upload audio files
  - Generate QR codes for participant registration
  - Presentation mode for beamer display

- **Participant Interface**
  - QR code registration
  - Mobile-optimized answer interface
  - Real-time round progression

## Tech Stack

- Vue.js 3 (Composition API)
- Vuetify 3 (Material Design)
- Pinia (State Management)
- Vue Router 4
- Axios (HTTP Client)
- Vite (Build Tool)

## Prerequisites

- Node.js 18+ and npm
- Backend API deployed and running

## Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env and add your API Gateway URL
# VITE_API_BASE_URL=https://your-api-gateway-url.execute-api.eu-central-1.amazonaws.com/prod
```

## Development

```bash
# Start development server
npm run dev

# Access at http://localhost:3000
```

## Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/
│   ├── admin/          # Admin-specific components
│   ├── participant/    # Participant components
│   ├── presentation/   # Presentation mode components
│   └── common/         # Shared components
├── views/
│   ├── admin/          # Admin views
│   └── participant/    # Participant views
├── stores/             # Pinia stores
├── services/           # API service
├── router/             # Vue Router configuration
└── plugins/            # Vuetify configuration
```

## Environment Variables

- `VITE_API_BASE_URL` - Backend API base URL

## Usage

### Admin Workflow

1. Login at `/admin/login`
2. Create a new quiz session
3. Add rounds with audio files and answers
4. Generate QR code for participants
5. Open presentation mode for beamer display

### Participant Workflow

1. Scan QR code or visit registration URL
2. Enter name to register
3. Answer questions as admin progresses through rounds

## Deployment

### AWS S3 + CloudFront

```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name
```

### Netlify

```bash
npm run build
# Deploy dist/ folder
```

### Vercel

```bash
npm run build
# Deploy dist/ folder
```

## License

MIT
