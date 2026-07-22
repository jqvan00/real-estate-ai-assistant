# AI Real Estate Assistant: GitHub + Sprint Plan

## Goal
Turn the current local starter into a real GitHub-backed project with working milestones, feature branches, and a staged build plan.

## Step 1: Put the project in Git
From the project root:

```bash
git init
git add .
git commit -m "Initial starter scaffold"
git branch -M main
```

Create a new GitHub repository, then connect it:

```bash
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

## Step 2: Add a branching workflow
Use one branch per sprint or feature:

- `sprint-1-ui`
- `sprint-2-property-api`
- `sprint-3-ai-chat`
- `sprint-4-reports-auth`
- `sprint-5-maps-enrichment`
- `sprint-6-investment-models`
- `sprint-7-voice-mobile-deploy`

Workflow:

```bash
git checkout -b sprint-1-ui
# work
git add .
git commit -m "Sprint 1: UI foundation"
git push -u origin sprint-1-ui
```

Open a pull request into `main` when a sprint is complete.

## Step 3: Recommended GitHub milestones
### Milestone 1: UI Foundation
- Responsive dashboard
- Property input form
- Verified facts card
- AI analysis card
- Loading and error states

### Milestone 2: Property Engine
- Real provider connectors
- Raw source storage
- Normalizer
- Verified profile endpoint

### Milestone 3: AI Assistant
- OpenAI integration
- Property-aware chat
- Conversation memory
- Saved question history

### Milestone 4: Reports and Accounts
- Login / auth
- Saved properties
- Report generation
- PDF export

### Milestone 5: Enrichment
- Maps
- Schools
- Flood
- Nearby places
- Commute

### Milestone 6: Investment Analysis
- Rent estimate
- Cash flow
- Cap rate
- ROI
- BRRRR / flip analysis placeholders

### Milestone 7: Voice, Mobile, Deploy
- Voice mode
- Mobile polish
- Docker
- Production deployment
- CI checks

## Step 4: API connection order
Build in this order so the app stays stable:

1. Keep the current demo engine working.
2. Replace one demo connector with one live provider.
3. Normalize the provider response into one verified schema.
4. Add a second provider.
5. Add conflict handling.
6. Feed the verified profile into chat.
7. Feed the verified profile into the report PDF.

## Step 5: Environment variables to prepare
Add these to `.env` as you get real keys:

```env
OPENAI_API_KEY=
ATTOM_API_KEY=
RENTCAST_API_KEY=
ESTATED_API_KEY=
REGRID_API_KEY=
GOOGLE_MAPS_API_KEY=
FEMA_API_KEY=
NOAA_API_KEY=
```

## Step 6: Best first coding order
1. GitHub repo + branch workflow
2. UI polish
3. One real property API
4. Normalizer
5. Chat
6. PDF reports
7. Rich enrichment data
8. Investment analysis
9. Voice and deployment

## Step 7: Definition of done for each sprint
A sprint is done only when:
- the app runs locally
- the feature is reachable in the UI
- the code is committed to Git
- the branch is merged cleanly
- the feature has at least one smoke test or manual validation step

## Immediate next move
Create the GitHub repository, push the current working local project, then start Sprint 1 on a branch called `sprint-1-ui`.
