# Admin User Guide: Music Quiz System

This guide explains how to use the Music Quiz system as an administrator. There are two types of administrators:

1. **Super Admin**: Manages tenants and tenant administrators
2. **Tenant Admin**: Manages quiz sessions within their organization

---

## Table of Contents

- [Super Admin Guide](#super-admin-guide)
- [Tenant Admin Guide](#tenant-admin-guide)
- [Common Tasks](#common-tasks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Super Admin Guide

Super admins have full system access and can manage multiple organizations (tenants).

### Logging In

1. Navigate to the admin login page
2. Enter your super admin credentials
3. Click "Login"
4. You'll be redirected to the super admin dashboard

### Managing Tenants

#### Creating a New Tenant

1. From the super admin dashboard, click **"Tenants"** in the navigation menu
2. Click the **"Create Tenant"** button
3. Fill in the tenant information:
   - **Name** (required): Organization name (e.g., "Acme Corporation")
   - **Description** (optional): Brief description of the organization
4. Click **"Create"**
5. The new tenant will appear in the tenant list

**Example:**
```
Name: Acme Corporation
Description: Corporate quiz events and team building
```

#### Viewing All Tenants

1. Click **"Tenants"** in the navigation menu
2. You'll see a table with all tenants showing:
   - Tenant name
   - Status (Active/Inactive)
   - Creation date
   - Number of admins
3. Use the search bar to filter tenants by name
4. Click on a tenant row to view details

#### Editing a Tenant

1. In the tenant list, click the **"Edit"** button next to the tenant
2. Update the tenant information:
   - Name
   - Description
   - Status (Active/Inactive)
3. Click **"Save Changes"**

**Note:** Deactivating a tenant prevents new quiz sessions from being created but doesn't delete existing data.

#### Deleting a Tenant

1. In the tenant list, click the **"Delete"** button next to the tenant
2. Confirm the deletion in the dialog
3. The tenant will be marked as inactive (soft delete)

**Warning:** Deleting a tenant will:
- Mark the tenant as inactive
- Prevent new sessions from being created
- Preserve existing data for historical purposes
- Block all tenant admin access

### Managing Tenant Administrators

#### Creating a Tenant Admin

1. Click **"Tenants"** in the navigation menu
2. Click on the tenant you want to add an admin to
3. Click the **"Admins"** tab
4. Click **"Create Admin"**
5. Fill in the admin information:
   - **Username** (required): Unique username for login
   - **Password** (required): Secure password (min 8 characters)
   - **Email** (optional): Admin's email address
6. Click **"Create"**

**Password Requirements:**
- Minimum 8 characters
- Mix of letters and numbers recommended
- Special characters recommended

#### Viewing Tenant Admins

1. Click **"Tenants"** in the navigation menu
2. Click on a tenant
3. Click the **"Admins"** tab
4. You'll see all admins for that tenant with:
   - Username
   - Email
   - Creation date
   - Last login

#### Editing a Tenant Admin

1. Navigate to the tenant's admin list
2. Click the **"Edit"** button next to the admin
3. Update the admin information:
   - Username
   - Email
   - Tenant assignment (to move admin to different tenant)
4. Click **"Save Changes"**

#### Resetting an Admin's Password

1. Navigate to the tenant's admin list
2. Click the **"Reset Password"** button next to the admin
3. Enter the new password
4. Click **"Reset"**
5. Inform the admin of their new password securely

#### Deleting a Tenant Admin

1. Navigate to the tenant's admin list
2. Click the **"Delete"** button next to the admin
3. Confirm the deletion
4. The admin will be removed and can no longer log in

**Warning:** This action cannot be undone. The admin will lose all access immediately.

### Super Admin Dashboard

The super admin dashboard provides an overview of:

- **Total Tenants**: Number of active tenants
- **Total Admins**: Number of tenant admins across all tenants
- **Total Sessions**: Number of quiz sessions across all tenants
- **Recent Activity**: Latest tenant and admin activities

---

## Tenant Admin Guide

Tenant admins manage quiz sessions within their organization.

### Logging In

1. Navigate to the admin login page
2. Enter your username and password
3. Click "Login"
4. You'll be redirected to your tenant's dashboard

**Note:** Your access is limited to your organization's data only.

### Dashboard Overview

The tenant admin dashboard shows:

- **Active Sessions**: Currently running quiz sessions
- **Total Participants**: Number of participants in your organization
- **Recent Sessions**: Latest quiz sessions
- **Quick Actions**: Shortcuts to common tasks

### Managing Quiz Sessions

#### Creating a New Quiz Session

1. From the dashboard, click **"Create Session"** or navigate to **"Sessions"** → **"Create New"**
2. Fill in the session details:
   - **Title** (required): Quiz session name (e.g., "80s Music Quiz")
   - **Description** (optional): Brief description of the quiz
3. Click **"Create Session"**
4. You'll be redirected to the session detail page

**Example:**
```
Title: 80s Music Quiz Night
Description: Test your knowledge of 80s hits! 10 rounds of classic songs.
```

#### Adding Rounds to a Session

1. Open the session detail page
2. Click **"Add Round"**
3. Upload or select an audio file:
   - Click **"Upload Audio"** to upload a new file
   - Or select from previously uploaded files
4. Enter the four answer options:
   - Answer 1
   - Answer 2
   - Answer 3
   - Answer 4
5. Select the correct answer (0-3)
6. Click **"Add Round"**
7. Repeat for up to 30 rounds

**Audio File Requirements:**
- Format: MP3, WAV, or OGG
- Maximum size: 10MB
- Recommended length: 15-30 seconds

**Tips:**
- Use clear, recognizable song clips
- Ensure audio quality is good
- Test audio playback before the quiz
- Make answer options challenging but fair

#### Uploading Audio Files

1. In the session detail page, click **"Add Round"**
2. Click **"Upload Audio"**
3. Select an audio file from your computer
4. Wait for the upload to complete
5. The file will be available for use in rounds

**Supported Formats:**
- MP3 (recommended)
- WAV
- OGG

#### Editing a Session

1. Navigate to **"Sessions"**
2. Click on the session you want to edit
3. Click **"Edit Session"**
4. Update the title or description
5. Click **"Save Changes"**

**Note:** You cannot edit rounds after they've been created. Delete and recreate if needed.

#### Deleting a Round

1. Open the session detail page
2. Find the round you want to delete
3. Click the **"Delete"** button next to the round
4. Confirm the deletion
5. Round numbers will be automatically adjusted

#### Starting a Quiz Session

1. Open the session detail page
2. Ensure all rounds are added
3. Click **"Start Session"**
4. The session status changes to "Active"
5. Share the QR code or registration link with participants

#### Generating QR Code for Registration

1. Open the session detail page
2. Click **"Generate QR Code"**
3. A QR code will be displayed
4. Options:
   - **Download**: Save QR code as image
   - **Print**: Print QR code for display
   - **Copy Link**: Copy registration URL to clipboard

**Using the QR Code:**
- Display on a screen for participants to scan
- Print and post in the venue
- Share in digital communications

#### Controlling Quiz Flow

1. Open the session detail page during an active session
2. Use the round controls:
   - **Start Round**: Begin the current round
   - **Play Audio**: Play the audio clip
   - **Show Answers**: Display answer options to participants
   - **End Round**: Close submissions and show results
   - **Next Round**: Move to the next round

**Typical Flow:**
1. Start Round → Audio plays automatically
2. Participants submit answers
3. End Round → Submissions close
4. View results and scoreboard
5. Next Round → Repeat

#### Viewing Participants

1. Open the session detail page
2. Click the **"Participants"** tab
3. You'll see all participants who have joined:
   - Name
   - Avatar
   - Current score
   - Number of correct answers
   - Join time

**Actions:**
- **Refresh**: Update participant list
- **Export**: Download participant list as CSV
- **Remove**: Remove a participant from the session (if needed)

#### Viewing Live Scoreboard

1. Open the session detail page
2. Click the **"Scoreboard"** tab
3. The scoreboard shows:
   - Participant rankings
   - Current scores
   - Number of correct answers
4. The scoreboard updates in real-time as participants submit answers

**Display Options:**
- **Full Screen**: Display scoreboard on a large screen
- **Auto-Refresh**: Automatically update every few seconds
- **Export**: Download scoreboard as PDF or image

#### Ending a Session

1. Open the session detail page
2. After all rounds are complete, click **"End Session"**
3. The session status changes to "Completed"
4. Final results are saved
5. Participants can still view their scores

**Note:** Ended sessions cannot be restarted. Create a new session for another quiz.

### Managing Participants

#### Viewing All Participants

1. Navigate to **"Participants"** in the menu
2. You'll see all participants in your organization:
   - Name
   - Avatar
   - Total sessions joined
   - Total points earned
   - Registration date

#### Searching Participants

1. In the participants list, use the search bar
2. Search by name
3. Results update as you type

#### Viewing Participant History

1. Click on a participant in the list
2. You'll see their participation history:
   - Sessions joined
   - Scores per session
   - Total points
   - Average performance

#### Removing a Participant

1. In the participants list, click the **"Remove"** button
2. Confirm the removal
3. The participant will be removed from all future sessions
4. Historical data is preserved

**Note:** This removes the participant from your organization. They would need to re-register to participate again.

### Reports and Analytics

#### Session Reports

1. Navigate to **"Reports"** → **"Sessions"**
2. Select a date range
3. View metrics:
   - Total sessions
   - Average participants per session
   - Average scores
   - Most popular sessions

#### Participant Reports

1. Navigate to **"Reports"** → **"Participants"**
2. View metrics:
   - Total participants
   - Active participants
   - Participation trends
   - Top performers

#### Exporting Data

1. In any report view, click **"Export"**
2. Choose format:
   - CSV
   - PDF
   - Excel
3. Download the file

---

## Common Tasks

### Preparing for a Quiz Event

1. **Create Session**: Set up the quiz session with title and description
2. **Add Rounds**: Upload audio files and create all rounds
3. **Test Audio**: Play each audio clip to ensure quality
4. **Generate QR Code**: Create QR code for participant registration
5. **Test Flow**: Do a test run with a colleague
6. **Start Session**: Activate the session before the event
7. **Display QR Code**: Show QR code for participants to scan

### Running a Live Quiz

1. **Welcome Participants**: Display QR code for registration
2. **Wait for Participants**: Monitor participant list
3. **Start First Round**: Click "Start Round"
4. **Monitor Submissions**: Watch as participants submit answers
5. **End Round**: Close submissions when time is up
6. **Show Scoreboard**: Display current rankings
7. **Continue**: Move to next round
8. **Final Results**: Show final scoreboard at the end

### Managing Multiple Sessions

1. **Use Clear Naming**: Name sessions with dates (e.g., "80s Quiz - Jan 20, 2024")
2. **Archive Old Sessions**: Mark completed sessions as archived
3. **Reuse Audio**: Previously uploaded audio files can be reused
4. **Template Sessions**: Create a template session and duplicate it

### Troubleshooting During a Quiz

#### Participants Can't Join

1. Check session status is "Active"
2. Verify QR code is correct
3. Check participant's internet connection
4. Provide manual registration link

#### Audio Not Playing

1. Check audio file was uploaded correctly
2. Verify browser supports audio format
3. Check device volume settings
4. Try refreshing the page

#### Scoreboard Not Updating

1. Click "Refresh" button
2. Check internet connection
3. Verify round has ended
4. Try reloading the page

---

## Best Practices

### Session Management

1. **Plan Ahead**: Create sessions well before the event
2. **Test Everything**: Test audio and flow before going live
3. **Clear Titles**: Use descriptive session titles
4. **Backup Audio**: Keep backup copies of audio files
5. **Monitor Participants**: Watch for issues during the quiz

### Audio Quality

1. **Use High Quality**: Upload high-quality audio files
2. **Consistent Volume**: Ensure all clips have similar volume
3. **Clear Clips**: Use recognizable portions of songs
4. **Appropriate Length**: 15-30 seconds is ideal
5. **Test Playback**: Always test before the event

### Participant Experience

1. **Clear Instructions**: Provide clear instructions to participants
2. **Test Registration**: Test the registration flow beforehand
3. **Monitor Chat**: If using chat, monitor for questions
4. **Fair Difficulty**: Balance easy and hard questions
5. **Celebrate Winners**: Acknowledge top performers

### Security

1. **Strong Passwords**: Use strong passwords for admin accounts
2. **Don't Share Credentials**: Keep admin credentials private
3. **Regular Logout**: Log out when finished
4. **Monitor Access**: Review admin activity logs
5. **Report Issues**: Report suspicious activity immediately

---

## Troubleshooting

### Login Issues

**Problem**: Can't log in
**Solutions**:
- Verify username and password are correct
- Check caps lock is off
- Clear browser cache and cookies
- Try a different browser
- Contact super admin for password reset

### Session Creation Issues

**Problem**: Can't create session
**Solutions**:
- Verify you're logged in as tenant admin
- Check your tenant is active
- Ensure you have proper permissions
- Try refreshing the page
- Contact super admin if issue persists

### Audio Upload Issues

**Problem**: Audio file won't upload
**Solutions**:
- Check file size is under 10MB
- Verify file format (MP3, WAV, OGG)
- Check internet connection
- Try a different file
- Clear browser cache

### Participant Issues

**Problem**: Participants can't see questions
**Solutions**:
- Verify round has started
- Check session is active
- Ensure participants are logged in
- Have participants refresh their page
- Check for browser compatibility issues

### Scoreboard Issues

**Problem**: Scoreboard not showing correct scores
**Solutions**:
- Click refresh button
- Verify all answers have been submitted
- Check round has ended
- Clear browser cache
- Contact support if issue persists

---

## Keyboard Shortcuts

### Session Management
- `Ctrl/Cmd + N`: Create new session
- `Ctrl/Cmd + S`: Save changes
- `Ctrl/Cmd + R`: Refresh participant list
- `Space`: Start/Stop audio playback
- `Enter`: Submit form

### Navigation
- `Ctrl/Cmd + H`: Go to dashboard
- `Ctrl/Cmd + L`: Go to sessions list
- `Ctrl/Cmd + P`: Go to participants
- `Ctrl/Cmd + Q`: Logout

---

## Getting Help

### Support Resources

1. **Documentation**: Check this guide and API documentation
2. **FAQ**: Review frequently asked questions
3. **Video Tutorials**: Watch tutorial videos
4. **Contact Support**: Email support@example.com
5. **Community Forum**: Join the community forum

### Reporting Issues

When reporting an issue, include:
- Your username (not password)
- Tenant name
- Session ID (if applicable)
- Description of the problem
- Steps to reproduce
- Screenshots if possible
- Browser and device information

### Feature Requests

To request new features:
1. Check if feature already exists
2. Search existing feature requests
3. Submit detailed feature request
4. Include use case and benefits
5. Vote on existing requests

---

## Appendix

### Glossary

- **Tenant**: An organization using the quiz system
- **Session**: A quiz event with multiple rounds
- **Round**: A single question in a quiz
- **Participant**: A user taking the quiz
- **Scoreboard**: Rankings of participants by score
- **QR Code**: Quick Response code for easy registration

### Limits and Quotas

- **Maximum Rounds per Session**: 30
- **Maximum Audio File Size**: 10MB
- **Maximum Session Title Length**: 100 characters
- **Maximum Description Length**: 500 characters
- **Concurrent Active Sessions**: Unlimited
- **Participants per Session**: Unlimited

### API Rate Limits

- **API Requests**: 100 per second
- **Burst Limit**: 200 requests
- **Audio Upload**: 10 per minute

---

## Updates and Changes

This guide is regularly updated. Check back for:
- New features
- Updated workflows
- Best practices
- Troubleshooting tips

**Last Updated**: January 2024
**Version**: 2.0 (Multi-Tenant)
