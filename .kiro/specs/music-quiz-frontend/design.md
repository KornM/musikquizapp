# Music Quiz Frontend Design Document

## Overview

The Music Quiz Frontend is a Vue.js 3 application with Vuetify 3 that provides two main interfaces:
1. **Admin Interface**: For creating and managing quiz sessions, with a presentation view for beamer display
2. **Participant Interface**: A mobile-optimized interface for answering quiz questions

The application follows a component-based architecture with Vue Router for navigation, Pinia for state management, and Axios for API communication.

## Technology Stack

- **Framework**: Vue.js 3 (Composition API)
- **UI Library**: Vuetify 3
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Build Tool**: Vite
- **QR Code**: qrcode.vue3
- **Audio**: HTML5 Audio API

## Architecture

### Project Structure

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/
│   │   └── styles/
│   │       └── main.css
│   ├── components/
│   │   ├── admin/
│   │   │   ├── SessionCard.vue
│   │   │   ├── SessionForm.vue
│   │   │   ├── RoundForm.vue
│   │   │   ├── RoundList.vue
│   │   │   ├── AudioUpload.vue
│   │   │   └── QRCodeModal.vue
│   │   ├── participant/
│   │   │   ├── AnswerButton.vue
│   │   │   └── RoundIndicator.vue
│   │   ├── presentation/
│   │   │   ├── AudioPlayer.vue
│   │   │   ├── AnswerDisplay.vue
│   │   │   └── RoundNavigation.vue
│   │   └── common/
│   │       ├── LoadingSpinner.vue
│   │       ├── ErrorAlert.vue
│   │       └── SuccessSnackbar.vue
│   ├── views/
│   │   ├── admin/
│   │   │   ├── LoginView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── SessionDetailView.vue
│   │   │   └── PresentationView.vue
│   │   └── participant/
│   │       ├── RegistrationView.vue
│   │       └── QuizView.vue
│   ├── router/
│   │   └── index.js
│   ├── stores/
│   │   ├── auth.js
│   │   ├── sessions.js
│   │   └── participant.js
│   ├── services/
│   │   └── api.js
│   ├── utils/
│   │   ├── validators.js
│   │   └── formatters.js
│   ├── plugins/
│   │   └── vuetify.js
│   ├── App.vue
│   └── main.js
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## Component Design

### Admin Components

#### 1. LoginView.vue
- Login form with username and password
- Form validation
- Error handling
- Redirects to dashboard on success

#### 2. DashboardView.vue
- Grid of session cards
- Create new session button
- Search/filter functionality
- Session status indicators

#### 3. SessionCard.vue
- Displays session title, description, round count
- Actions: View details, Present, Generate QR
- Status badge (draft/active/completed)

#### 4. SessionDetailView.vue
- Session information display
- List of rounds
- Add round button
- Edit session button
- Generate QR code button

#### 5. RoundForm.vue
- Audio file upload (drag & drop)
- 4 answer input fields
- Correct answer selector (radio buttons)
- Submit button
- Validation

#### 6. AudioUpload.vue
- Drag and drop zone
- File input fallback
- Upload progress bar
- Audio preview player
- File type/size validation

#### 7. QRCodeModal.vue
- QR code display
- Registration URL
- Download QR code button
- Copy URL button

#### 8. PresentationView.vue
- Fullscreen mode
- Large audio player
- Answer options display (A, B, C, D)
- Round navigation (prev/next)
- Reveal answer button
- Exit presentation button

### Participant Components

#### 9. RegistrationView.vue
- Session title and description
- Name input field
- Register button
- Validation

#### 10. QuizView.vue
- Round indicator (e.g., "Round 3 of 10")
- 4 large answer buttons (A, B, C, D)
- Selected answer highlight
- Waiting for next round indicator

#### 11. AnswerButton.vue
- Large, touch-friendly button
- Letter label (A, B, C, D)
- Answer text
- Selected state styling
- Disabled state

### Common Components

#### 12. LoadingSpinner.vue
- Centered spinner
- Optional loading message

#### 13. ErrorAlert.vue
- Error message display
- Dismiss button
- Auto-dismiss option

#### 14. SuccessSnackbar.vue
- Success message
- Auto-dismiss after 3 seconds

## State Management (Pinia)

### Auth Store
```javascript
{
  state: {
    token: null,
    isAuthenticated: false,
    user: null
  },
  actions: {
    login(username, password),
    logout(),
    checkAuth()
  }
}
```

### Sessions Store
```javascript
{
  state: {
    sessions: [],
    currentSession: null,
    loading: false,
    error: null
  },
  actions: {
    fetchSessions(),
    fetchSession(id),
    createSession(data),
    addRound(sessionId, roundData),
    uploadAudio(file, sessionId)
  }
}
```

### Participant Store
```javascript
{
  state: {
    participantId: null,
    participantToken: null,
    sessionId: null,
    currentRound: 1,
    selectedAnswers: {}
  },
  actions: {
    register(sessionId, name),
    submitAnswer(roundNumber, answer),
    nextRound()
  }
}
```

## Routing

```javascript
const routes = [
  {
    path: '/admin/login',
    component: LoginView
  },
  {
    path: '/admin/dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/sessions/:id',
    component: SessionDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/sessions/:id/present',
    component: PresentationView,
    meta: { requiresAuth: true }
  },
  {
    path: '/register',
    component: RegistrationView
  },
  {
    path: '/quiz/:sessionId',
    component: QuizView
  },
  {
    path: '/',
    redirect: '/admin/login'
  }
]
```

## API Service

### API Client Configuration
```javascript
// services/api.js
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for auth token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
      router.push('/admin/login')
    }
    return Promise.reject(error)
  }
)
```

### API Methods
```javascript
export default {
  // Admin Auth
  login(username, password),
  
  // Sessions
  getSessions(),
  getSession(id),
  createSession(data),
  
  // Rounds
  addRound(sessionId, roundData),
  
  // Audio
  uploadAudio(file, sessionId),
  getAudioUrl(audioKey),
  
  // QR Code
  getQRData(sessionId),
  
  // Participants
  registerParticipant(sessionId, name)
}
```

## UI/UX Design

### Color Scheme (Vuetify Theme)
```javascript
{
  themes: {
    light: {
      primary: '#1976D2',    // Blue
      secondary: '#424242',  // Grey
      accent: '#82B1FF',     // Light Blue
      error: '#FF5252',      // Red
      info: '#2196F3',       // Blue
      success: '#4CAF50',    // Green
      warning: '#FFC107'     // Amber
    }
  }
}
```

### Responsive Breakpoints
- **Mobile**: < 600px (xs)
- **Tablet**: 600px - 960px (sm, md)
- **Desktop**: > 960px (lg, xl)

### Admin Interface Layout
- **Desktop**: Sidebar navigation + main content area
- **Mobile**: Bottom navigation + hamburger menu

### Participant Interface Layout
- **All devices**: Full-screen, centered content
- Large touch targets (minimum 48x48px)

## Data Flow

### Admin Session Creation Flow
1. Admin logs in → Token stored in localStorage
2. Admin creates session → POST to API
3. Session added to store → Dashboard updates
4. Admin adds rounds → Upload audio → POST audio → POST round
5. Rounds displayed in session detail

### Participant Quiz Flow
1. Participant scans QR code → Redirects to registration
2. Participant enters name → POST to API
3. Token stored → Redirected to quiz view
4. Participant selects answer → Stored locally
5. Admin advances round → Participant sees next round

### Presentation Flow
1. Admin opens presentation view → Fullscreen
2. Admin plays audio → HTML5 Audio API
3. Admin shows answers → Display on screen
4. Admin reveals correct answer → Highlight correct option
5. Admin navigates to next round

## Error Handling

### API Errors
- Network errors: Display retry button
- 401 Unauthorized: Redirect to login
- 404 Not Found: Display "not found" message
- 500 Server Error: Display generic error message

### Form Validation
- Required fields: "This field is required"
- Invalid format: "Please enter a valid [field]"
- File upload: "File must be MP3, WAV, or OGG"
- Max file size: "File must be less than 10MB"

### User Feedback
- Loading states: Spinner overlay
- Success: Green snackbar (3s auto-dismiss)
- Error: Red alert with dismiss button
- Info: Blue snackbar

## Security

### Token Storage
- JWT stored in localStorage
- Token included in Authorization header
- Token validated on protected routes

### Route Guards
```javascript
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/admin/login')
  } else {
    next()
  }
})
```

## Performance Optimization

### Code Splitting
- Lazy load routes
- Lazy load heavy components (QR code, audio player)

### Asset Optimization
- Compress images
- Use WebP format where supported
- Lazy load images

### API Optimization
- Cache session list
- Debounce search input
- Pagination for large lists

## Accessibility

### ARIA Labels
- All buttons have aria-label
- Form inputs have aria-describedby for errors
- Loading states have aria-live regions

### Keyboard Navigation
- Tab order follows visual order
- Enter key submits forms
- Escape key closes modals
- Arrow keys navigate lists

### Focus Management
- Visible focus indicators
- Focus trapped in modals
- Focus restored after modal close

## Testing Strategy

### Unit Tests
- Component rendering
- Store actions and mutations
- Utility functions
- Form validation

### Integration Tests
- API service methods
- Router navigation
- Store integration with components

### E2E Tests
- Admin login flow
- Session creation flow
- Participant registration flow
- Quiz playback flow

## Deployment

### Build Configuration
```javascript
// vite.config.js
export default {
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser'
  }
}
```

### Environment Variables
```
VITE_API_BASE_URL=https://your-api-gateway-url.com/prod
```

### Hosting Options
- AWS S3 + CloudFront
- Netlify
- Vercel
- Firebase Hosting

## Future Enhancements

- Real-time updates using WebSockets
- Participant leaderboard
- Quiz analytics dashboard
- Multi-language support
- Dark mode
- Offline support with PWA
