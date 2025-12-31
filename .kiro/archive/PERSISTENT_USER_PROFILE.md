# Persistent User Profile Across Sessions

## Overview
Enhanced the participant registration system to remember user profiles (name and avatar) across all quiz sessions. Users only need to set their name and avatar once, and it will be automatically loaded for all future quizzes.

## Changes Made

### Frontend - Register View (`frontend/src/views/participant/RegisterView.vue`)

#### 1. Profile Loading on Mount
- Added logic to load saved profile from localStorage
- Checks for `userProfileName` and `userProfileAvatar`
- Pre-fills registration form if profile exists
- Shows "Welcome back!" message for returning users

#### 2. Profile Saving on Registration
- Saves user profile to persistent localStorage keys:
  - `userProfileName` - User's display name
  - `userProfileAvatar` - Selected emoji avatar
- These keys are separate from session-specific keys
- Profile persists across browser sessions and different quizzes

#### 3. User Experience Enhancement
- Added info alert: "Welcome back! Your profile has been loaded."
- Only shown when existing profile is detected
- Users can still modify their name/avatar before joining

## How It Works

### First Time User
1. User visits registration page
2. Enters name and selects avatar
3. Clicks "Join Quiz"
4. Profile saved to:
   - Session-specific: `participantId`, `participantName`, `participantAvatar`
   - Global profile: `userProfileName`, `userProfileAvatar`
5. Joins the quiz

### Returning User (Same or Different Session)
1. User visits registration page
2. **Name and avatar automatically loaded** from saved profile
3. Sees "Welcome back!" message
4. Can modify name/avatar if desired
5. Clicks "Join Quiz"
6. Profile updated if changed

## LocalStorage Structure

### Session-Specific (per quiz session)
```javascript
localStorage.setItem("participantId", participantId);      // Unique per session
localStorage.setItem("participantToken", token);            // Session token
localStorage.setItem("participantName", name);              // Current session name
localStorage.setItem("participantAvatar", avatar);          // Current session avatar
```

### Global Profile (across all sessions)
```javascript
localStorage.setItem("userProfileName", name);              // Persistent name
localStorage.setItem("userProfileAvatar", avatar);          // Persistent avatar
```

## Benefits

✅ **Better UX** - Users don't need to re-enter their name every time
✅ **Consistency** - Same identity across multiple quiz sessions
✅ **Flexibility** - Users can still change their profile for specific sessions
✅ **No Backend Changes** - Pure frontend enhancement
✅ **Privacy Friendly** - Data stored locally, not on server
✅ **Instant** - No API calls needed to load profile

## User Scenarios

### Scenario 1: Regular Participant
- Joins first quiz: Sets name "Alice" and avatar "😀"
- Joins second quiz: Name and avatar pre-filled
- Joins third quiz: Name and avatar pre-filled
- Result: Seamless experience across all quizzes

### Scenario 2: Participant Wants Different Identity
- Has saved profile: "Alice" with "😀"
- Joins new quiz: Profile pre-filled
- Changes to "Alice (Team A)" with "🦸"
- Joins quiz with new identity
- Global profile updated to new values

### Scenario 3: Multiple Devices
- Desktop: Profile saved as "Alice" with "😀"
- Mobile: Needs to set profile again (different device)
- Each device maintains its own profile
- This is expected behavior for localStorage

## Technical Details

### Profile Detection
```javascript
const savedName = localStorage.getItem("userProfileName");
const savedAvatar = localStorage.getItem("userProfileAvatar");

if (savedName && savedAvatar) {
  // Load existing profile
  name.value = savedName;
  selectedAvatar.value = savedAvatar;
  hasExistingProfile.value = true;
}
```

### Profile Persistence
```javascript
// Save to both session-specific and global storage
localStorage.setItem("participantName", name.value);        // Session
localStorage.setItem("participantAvatar", selectedAvatar.value);  // Session
localStorage.setItem("userProfileName", name.value);        // Global
localStorage.setItem("userProfileAvatar", selectedAvatar.value);  // Global
```

## Clearing Profile

Users can clear their saved profile by:
1. **Browser Settings**: Clear site data/localStorage
2. **Developer Console**: 
   ```javascript
   localStorage.removeItem("userProfileName");
   localStorage.removeItem("userProfileAvatar");
   ```

## Future Enhancements

Potential improvements:
- Add "Clear Profile" button on registration page
- Show profile history/statistics
- Allow multiple saved profiles
- Sync profiles across devices (requires backend)
- Profile pictures instead of just emojis
- Nickname suggestions based on previous sessions

## Deployment

No deployment needed! This is a frontend-only change that works immediately after building:

```bash
cd frontend
npm run build
../scripts/deploy-frontend.sh
```

## Testing

Test scenarios:
- [ ] First-time user: Profile form is empty
- [ ] Returning user: Profile pre-filled with saved data
- [ ] Modify profile: Changes are saved for next session
- [ ] Clear localStorage: Profile form is empty again
- [ ] Multiple sessions: Same profile across different quizzes
- [ ] Different browsers: Each maintains separate profile

## Backward Compatibility

✅ **Fully backward compatible**
- Existing users without saved profiles work normally
- No breaking changes to registration flow
- Session-specific storage still works as before
- No backend changes required
