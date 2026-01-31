# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Security Considerations

**Note: MVP is for local/personal use - not production-ready security**

### Authentication Strategy

**Current Implementation (MVP - Email-Only):**
- **No passwords** - Users register and login with email address only
- Email is used as unique identifier to find/create user accounts
- Session-based authentication using Flask sessions
- Suitable for local/personal deployment only
- **Not secure for public deployment** - anyone with an email can access that account

**How it works:**
1. **Register:** User enters email → System creates user account or finds existing
2. **Login:** User enters email → System finds user and creates session
3. **Session:** User remains authenticated via session cookie

**Future Authentication Options (Not Implemented Yet):**
- **Magic Link:** Email-based passwordless authentication
  - User enters email → receives login link → clicks to authenticate
  - Links expire after 15 minutes
  - Secure for public deployment
- **Social Authentication:** OAuth providers (Google, GitHub, etc.)
  - One-click sign in with existing accounts
  - No password management needed
- **Single Sign-On (SSO):** Enterprise authentication
  - SAML or OAuth2 integration
  - Centralized identity management

**Why Email-Only for MVP:**
- Simplifies initial development and testing
- Sufficient for local/personal use
- Easy to migrate to magic link later (same email-based flow)
- No password management complexity
- Faster iteration on core features

**Migration Path:**
```
Current:     Email only (no verification)
    ↓
Step 1:      Magic link (email verification)
    ↓
Step 2:      Add social auth (Google, GitHub)
    ↓
Step 3:      Add SSO for enterprise (optional)
```

### Security Best Practices (Current Implementation)

- **CSRF:** Token validation for state-changing requests
- **File uploads:** Strict validation (file type, size limits, MIME check)
  - Only accept PNG, JPG, GIF for image imports
  - Max file size: 10MB (configurable)
- **Rate limiting:** On save endpoint (prevent abuse)
  - Max 100 saves per minute per user
- **Access control:** Users can only access their own projects
  - Validate user_id matches project.user_id on all operations
- **Input validation:**
  - Grid dimensions: max reasonable size (e.g., 1000×1000)
  - Palette size: max 256 colors
  - Layer count: max 10 layers per project

## Performance Targets

- **Grid rendering:** 60fps for grids up to 200×200
- **Save latency:** <200ms for typical diff (10-100 cell changes)
- **Load time:** <500ms for project load (full state decompress + parse)
- **Network payload:** Typical diff ~1-5KB gzipped
