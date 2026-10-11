# Production checklist (fill in as you test)

## Deploy
- [ ] Repo pushed to GitHub, imported in Vercel
- [ ] Env vars set for **Production** only (none needed for offline mode; `ANTHROPIC_API_KEY` if enabling Claude)
- [ ] Spend limit set in the Anthropic Console (if a key is used)
- [ ] `<url>/health` returns `{"ok": true, ...}`
- [ ] Optional: custom domain added and HTTPS works

## Full flow on the production URL
- [ ] Home, Bakery, Coffee, Flowers, Gallery, Our story all load, CSS and JS applied (not unstyled)
- [ ] Chat: "How much is a flat white?" -> 85 CZK; "Do you have wifi?" -> "I'm not sure"
- [ ] Order form: bad date shows an error; a valid request shows a reference number
- [ ] 3D designer loads when scrolled into view and rotates

## Cross-browser pass (note what you saw)
| Browser | Pages | Chat | Order form | 3D designer | Notes |
|---|---|---|---|---|---|
| Chrome (desktop) | | | | | |
| Firefox (desktop) | | | | | |
| Safari (macOS) | | | | | |
| Mobile Safari (iPhone) | | | | | |

## Abuse check
- [ ] Sending 31 chat requests in a minute from one browser returns the "asking very fast" message
- [ ] An oversized message is cut off, not crashing the app

## Git history
- [ ] History cleaned (see commit message guide: Conventional Commits 1.0.0)
- [ ] No `.env` or API key anywhere in history (`git log -p | grep -i "sk-ant"` finds nothing)
