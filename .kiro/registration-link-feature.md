# Participant Registration Link on Dashboard

## Date: December 30, 2024

## Overview

Added a prominent participant registration section to the admin dashboard, making it easy for admins to share the registration link with participants.

## Changes Made

### Frontend - Dashboard View

**Updated: `frontend/src/views/admin/DashboardView.vue`**

**Added Components:**
1. **Registration Card** - Prominent card at top of dashboard
   - Shows registration URL
   - Copy link button
   - Show QR code button
   - Clean, professional design

2. **QR Code Modal** - Dialog showing registration QR code
   - Large, scannable QR code
   - Registration URL displayed
   - Copy link button
   - Close button

**Added Logic:**
- `registrationUrl` - Computed property that generates registration URL with tenant ID
- `generateRegistrationQR()` - Generates QR code using qrcode library
- `copyRegistrationLink()` - Copies URL to clipboard with success feedback
- `showRegistrationQR` - Controls QR modal visibility

**Added Styling:**
- `.registration-card` - Gradient background with purple accent border
- `.qr-code-container` - Centered container with shadow
- `.qr-code-image` - Responsive QR code image

## Features

### Registration Card
- **Location**: Top of dashboard, above global leaderboard
- **Content**:
  - Icon and title
  - Description text
  - Registration URL (read-only text field)
  - "Copy Link" button (primary)
  - "Show QR Code" button (outlined)

### QR Code Modal
- **Trigger**: Click "Show QR Code" button
- **Content**:
  - Large QR code (300x300px)
  - Purple and white color scheme
  - Registration URL
  - Copy link button
  - Close button

### Copy to Clipboard
- Uses modern `navigator.clipboard` API
- Shows success snackbar: "Registration link copied to clipboard!"
- Handles errors gracefully

## Registration URL Format

```
https://your-domain.com/register?tenantId=<tenant-id>
```

The URL includes the tenant ID so participants are automatically registered to the correct tenant.

## User Flow

### Admin:
1. Login to dashboard
2. See registration card at top
3. Click "Copy Link" → Link copied to clipboard
4. Share link via email, chat, etc.
5. OR click "Show QR Code" → Display QR code
6. Participants scan QR code or use link

### Participant:
1. Receive link or scan QR code
2. Opens registration page with tenant ID pre-filled
3. Enter name and choose avatar
4. Register and join lobby
5. Browse and join active quiz sessions

## Benefits

1. **Easy Access**: Registration link always visible on dashboard
2. **Multiple Sharing Options**: Copy link or show QR code
3. **Professional**: Clean, modern design
4. **User-Friendly**: One-click copy, clear instructions
5. **Mobile-Friendly**: QR codes work great for mobile registration

## Dependencies

Uses the `qrcode` npm package (already installed in the project) to generate QR codes dynamically.

## Testing Checklist

- [ ] Registration card displays on dashboard
- [ ] Copy link button copies URL to clipboard
- [ ] Success message shows after copying
- [ ] Show QR Code button opens modal
- [ ] QR code displays correctly
- [ ] QR code scans and opens registration page
- [ ] Registration URL includes correct tenant ID
- [ ] Copy link from modal works
- [ ] Close button closes modal
- [ ] Responsive design works on mobile

## Screenshots

**Registration Card:**
- Prominent placement at top of dashboard
- Purple accent color matching app theme
- Clear call-to-action buttons

**QR Code Modal:**
- Large, scannable QR code
- Clean white background
- Easy to share via screen share

---

**Status**: Complete and ready to use
**No deployment required**: Frontend-only changes
