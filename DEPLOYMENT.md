# Testing deployment

This setup produces one HTTPS Vercel link that testers can open on a phone,
tablet, or desktop. The Next.js frontend runs on Vercel, while the FastAPI API
and PostgreSQL database run on Render.

## Before deploying

1. Rotate any API keys that have been pasted into chats or other tools.
2. Keep `.env` and `.env.local` files untracked.
3. Commit and push the tested project to GitHub.

## 1. Deploy the backend and database on Render

1. Sign in to Render and choose **New > Blueprint**.
2. Connect the GitHub repository.
3. Render will detect the root `render.yaml`.
4. Enter each secret requested by the Blueprint.
5. For `CORS_ORIGINS`, temporarily enter the future Vercel origin if known.
   Otherwise enter a placeholder such as `https://replace-after-vercel.vercel.app`
   and update it after step 2.
6. Deploy and copy the API URL, such as
   `https://real-estate-ai-assistant-api.onrender.com`.
7. Confirm that opening the API URL returns `"status": "ok"`.

## 2. Deploy the frontend on Vercel

1. In Vercel choose **Add New > Project** and import the same repository.
2. Set **Root Directory** to `frontend`.
3. Leave the detected Next.js build settings in place.
4. Add:

   `NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-API.onrender.com`

5. Deploy and copy the Vercel HTTPS URL.

## 3. Finish the connection

1. In Render, change `CORS_ORIGINS` to the exact Vercel origin, with no
   trailing slash:

   `https://YOUR-APP.vercel.app`

2. If Vercel provides multiple permanent domains, list them comma-separated.
3. Redeploy the Render service.
4. Redeploy Vercel if its API URL environment variable changed.

## Phone testing

Send testers only the Vercel URL. It works in Safari and Chrome without an
installation. Ask testers to check property search, the summary, AI Assistant,
audio controls, and the affordability calculator.

For microphone or audio features, keep the site on HTTPS and ask testers to
allow browser microphone/audio permissions when prompted.

## Feedback checklist

Ask testers to include:

- Phone model and browser
- Address or listing URL tested
- The screen and action where a problem occurred
- Screenshot or screen recording
- Whether the issue happens every time

## Important testing limitations

- The mortgage rate is a national weekly benchmark, not an individual quote.
- Affordability results are educational estimates, not lending decisions.
- Property data availability depends on configured third-party providers.
- Monitor API usage and costs while the testing link is shared.
