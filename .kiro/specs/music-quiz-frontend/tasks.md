# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Initialize Vite + Vue 3 project
  - Install Vuetify 3, Vue Router, Pinia, Axios, qrcode.vue3
  - Configure Vuetify plugin with theme
  - Set up project directory structure
  - _Requirements: All_

- [x] 2. Configure routing and navigation guards
  - Create router configuration with all routes
  - Implement authentication guard for admin routes
  - Set up route meta fields
  - _Requirements: 1.5_

- [x] 3. Create API service layer
  - Create Axios instance with base configuration
  - Implement request interceptor for auth token
  - Implement response interceptor for error handling
  - Create API methods for all endpoints
  - _Requirements: 1.2, 8.1_

- [x] 4. Implement Pinia stores
- [x] 4.1 Create auth store
  - Implement state for token and authentication status
  - Create login action
  - Create logout action
  - Create checkAuth action
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 4.2 Create sessions store
  - Implement state for sessions list and current session
  - Create fetchSessions action
  - Create fetchSession action
  - Create createSession action
  - Create addRound action
  - Create uploadAudio action
  - _Requirements: 2.1, 2.2, 3.1, 10.3_

- [x] 4.3 Create participant store
  - Implement state for participant data and answers
  - Create register action
  - Create submitAnswer action
  - Create nextRound action
  - _Requirements: 5.4, 7.3_

- [x] 5. Create common components
- [x] 5.1 Create LoadingSpinner component
  - Implement centered spinner with Vuetify
  - Add optional loading message prop
  - _Requirements: 9.1_

- [x] 5.2 Create ErrorAlert component
  - Implement error display with Vuetify alert
  - Add dismiss functionality
  - Add auto-dismiss option
  - _Requirements: 9.3_

- [x] 5.3 Create SuccessSnackbar component
  - Implement success message with Vuetify snackbar
  - Add auto-dismiss after 3 seconds
  - _Requirements: 9.2_

- [x] 6. Implement admin authentication
- [x] 6.1 Create LoginView component
  - Create login form with username and password fields
  - Implement form validation
  - Connect to auth store login action
  - Handle login errors
  - Redirect to dashboard on success
  - _Requirements: 1.1, 1.2, 9.4, 9.5_

- [x] 7. Implement admin dashboard
- [x] 7.1 Create DashboardView component
  - Create layout with app bar and main content
  - Implement logout button
  - Add create session button
  - Display sessions grid
  - _Requirements: 2.1, 1.4_

- [x] 7.2 Create SessionCard component
  - Display session title, description, round count
  - Add status badge
  - Implement action buttons (View, Present, QR)
  - _Requirements: 2.3_

- [x] 7.3 Create SessionForm dialog
  - Create form with title and description fields
  - Implement validation
  - Connect to sessions store createSession action
  - Handle success and error states
  - _Requirements: 2.2, 9.4, 9.5_

- [ ] 8. Implement session detail view
- [x] 8.1 Create SessionDetailView component
  - Display session information
  - Add generate QR button
  - Add present button
  - Display rounds list
  - Add "Add Round" button
  - _Requirements: 2.4, 3.6_

- [x] 8.2 Create RoundList component
  - Display rounds in order
  - Show round number, answers, correct answer indicator
  - _Requirements: 3.6_

- [x] 8.3 Create RoundForm component
  - Create form with audio upload and answer fields
  - Implement 4 answer input fields
  - Add correct answer selector (radio buttons)
  - Implement validation
  - Connect to sessions store addRound action
  - _Requirements: 3.1, 3.3, 3.4, 9.4, 9.5_

- [x] 8.4 Create AudioUpload component
  - Implement drag and drop zone
  - Add file input fallback
  - Display upload progress
  - Add audio preview player
  - Validate file type and size
  - Connect to sessions store uploadAudio action
  - _Requirements: 3.2, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 9. Implement QR code generation
- [x] 9.1 Create QRCodeModal component
  - Generate QR code using qrcode.vue3
  - Display registration URL
  - Add download QR code button
  - Add copy URL button
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 10. Implement presentation view
- [x] 10.1 Create PresentationView component
  - Implement fullscreen mode
  - Display round number and total
  - Add exit presentation button
  - Integrate audio player and answer display
  - Add round navigation
  - _Requirements: 6.1, 6.2, 6.5_

- [ ] 10.2 Create AudioPlayer component
  - Implement HTML5 audio player
  - Add play/pause controls
  - Display audio progress
  - _Requirements: 6.3_

- [ ] 10.3 Create AnswerDisplay component
  - Display 4 answer options prominently
  - Implement reveal correct answer functionality
  - Highlight correct answer when revealed
  - _Requirements: 6.4, 6.6_

- [ ] 10.4 Create RoundNavigation component
  - Add previous/next round buttons
  - Disable buttons at boundaries
  - _Requirements: 6.5_

- [ ] 11. Implement participant registration
- [ ] 11.1 Create RegistrationView component
  - Display session title and description
  - Create name input form
  - Implement validation
  - Connect to participant store register action
  - Redirect to quiz view on success
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.4, 9.5_

- [ ] 12. Implement participant quiz interface
- [ ] 12.1 Create QuizView component
  - Display round indicator
  - Integrate answer buttons
  - Show waiting indicator between rounds
  - _Requirements: 7.1, 7.5_

- [ ] 12.2 Create AnswerButton component
  - Create large, touch-friendly button
  - Display letter label and answer text
  - Implement selected state styling
  - Implement disabled state
  - Connect to participant store submitAnswer action
  - _Requirements: 7.2, 7.3, 7.4_

- [ ] 12.3 Create RoundIndicator component
  - Display current round number
  - Display total rounds
  - _Requirements: 7.1_

- [ ] 13. Implement responsive design
  - Configure Vuetify breakpoints
  - Test layouts on mobile, tablet, desktop
  - Optimize touch targets for mobile
  - Test portrait and landscape orientations
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 14. Implement error handling
  - Add error handling to all API calls
  - Display appropriate error messages
  - Implement retry logic for network errors
  - Handle 401 redirects to login
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 15. Implement accessibility features
  - Add ARIA labels to all interactive elements
  - Implement keyboard navigation
  - Add focus indicators
  - Test with screen reader
  - Ensure color contrast ratios
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 16. Configure environment variables
  - Create .env file with API base URL
  - Update API service to use environment variable
  - Document environment setup in README
  - _Requirements: All_

- [ ] 17. Create build configuration
  - Configure Vite build settings
  - Set up production optimizations
  - Configure asset handling
  - _Requirements: All_

- [ ] 18. Test admin workflow end-to-end
  - Test login flow
  - Test session creation
  - Test round creation with audio upload
  - Test QR code generation
  - Test presentation mode
  - _Requirements: 1.1, 2.2, 3.1, 4.1, 6.1_

- [ ] 19. Test participant workflow end-to-end
  - Test registration via QR code
  - Test answer submission
  - Test round progression
  - _Requirements: 5.1, 7.2, 7.3_

- [ ] 20. Create README documentation
  - Document installation steps
  - Document development setup
  - Document build and deployment
  - Document environment variables
  - Add API endpoint configuration instructions
  - _Requirements: All_
