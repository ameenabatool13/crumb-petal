# Final package index (Assignment 8.2)

Every deliverable from the track, in one place. Fill the blanks, then check each line is reachable.

| # | Deliverable | Where | Status |
|---|---|---|---|
| 1 | README (what it does, setup, usage, architecture, v2 eval, limitations, AI-use line) | [`../README.md`](../README.md) | Written. **You:** edit the "Built with AI" paragraph |
| 2 | Demo video (3-5 min, live run, no slides) | URL: ______ | **You:** record with [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |
| 3 | Showcase thread post (README + video link) | URL: ______ | **You** |
| 4 | Code | [`../app.py`](../app.py), [`../chatbot.py`](../chatbot.py), `../templates/`, `../public/static/` | Done |
| 5 | v1 / v2 eval | [`../eval/results_v1_local.md`](../eval/results_v1_local.md), [`../eval/results_v2_local.md`](../eval/results_v2_local.md) | Done (offline engine). Optional: run Claude engine |
| 6 | 3D experience + perf note | `/flowers` page, README section | Built. **You:** fill the 4 measurements |
| 7 | Retrospective (500-800 words) | `docs/RETROSPECTIVE.md` | **You:** use [`RETROSPECTIVE_GUIDE.md`](RETROSPECTIVE_GUIDE.md) |
| 8 | Hours log | FlyRank portal | **You:** complete in the portal |
| 9 | Live site on the FlyRank domain | URL: ______ | **You:** deploy (see below) |
| 10 | Build-in-public post (one real decision, one real limitation) | URL: ______ | **You:** start from [`BUILD_IN_PUBLIC_DRAFT.md`](BUILD_IN_PUBLIC_DRAFT.md) |
| 11 | Final review checkpoint | Submit via written sign-off or scheduled session | **You** |

## Evaluation criteria check (pass / revise)

- [ ] Every deliverable present and reachable from this index
- [ ] Retrospective specific to your build, not generic
- [ ] Hours log complete and plausible against timestamps
- [ ] Site live on the FlyRank domain and navigable in five minutes
- [ ] Post explains one real decision and one real limitation

## Deploying

The site is a Flask app deployed on Vercel. See the README section "Deploying (Vercel)" and `DEPLOY_CHECKLIST.md`. Never commit `.env`. Check `/health` after deploy.
