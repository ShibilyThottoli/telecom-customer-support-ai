# Public deployment

The frontend is a static Vite/React site; the backend is FastAPI. The backend
invokes the existing Amazon Bedrock AgentCore Runtime. For a no-cost hosting
setup, this guide uses Cloudflare Pages, Render's Free web service, and
Supabase's Free PostgreSQL project. The backend uses PostgreSQL when
`DATABASE_URL` is set and falls back to local SQLite for development.

## Hosting and costs

- **Cloudflare Pages:** Free plan for the static frontend. Check the current
  [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
  before launch.
- **Render FastAPI service:** The included Blueprint uses the Free web-service
  plan. Free services sleep after 15 minutes without traffic; waking one can
  take about a minute. The service URL remains public, but first requests after
  sleep can be slow. See [Render's free instance documentation](https://render.com/docs/free).
- **PostgreSQL:** Use Supabase Free and paste its connection string into
  Render's `DATABASE_URL` secret. Its free quota and inactivity policies can
  change; free projects may be paused after inactivity, so check the current
  [Supabase pricing and plan limits](https://supabase.com/pricing) and resume
  the project if that happens.
- **Expected hosting cost:** **US$0/month** while Cloudflare Pages, Render
  Free, and Supabase Free remain within their free limits. This is not a
  guarantee that the chatbot's AI usage is free.
- **Separate usage costs:** Amazon Bedrock AgentCore Runtime, AWS Secrets
  Manager/network usage, and the model provider may incur charges. The current
  AgentCore integration is retained. Check AWS and model provider billing and
  set budget alerts before sharing the site.

Cloudflare Pages provides a stable `*.pages.dev` address. Render provides a
stable `*.onrender.com` API address. A custom domain is optional and may have
registration costs.

## Connect the project to GitHub

The workspace now has one root Git repository for the monorepo. The original
backend `.git` metadata was preserved in a sibling backup folder named
`ShibilyFAQAssistant-backend-git-backup`; no files have been committed or
pushed. Review the root repository's pending files, then create a GitHub
repository and push this project so Render can read `render.yaml` and Cloudflare
Pages can build from `frontend/`. Keep the GitHub repository private if you
don't want to publish the source. Never commit `.env` files, SQLite databases,
AWS keys, or the Groq API key.

## Create the free PostgreSQL database

1. Create a Supabase project on its Free plan.
2. In **Project Settings → Database → Connection string**, choose the
   Session pooler connection string and copy it. Use the complete URI,
   including its password and SSL settings, as a secret; do not commit it.
3. Keep the Supabase project region close to the Render service region where
   possible. Free-tier databases may pause due to inactivity and have limited
   storage/compute; check current plan limits and keep a backup of any memory
   you need to retain.

## Publish the API on Render

1. Push the project to a GitHub repository after resolving the repository
   layout above.
2. In Render, choose **New → Blueprint**, connect the repository, and select
   `render.yaml` at the repository root.
3. Keep the API web service on Free to minimize hosting costs.
4. Enter the prompted values in Render's environment-variable form:
   - `DATABASE_URL`: the Supabase PostgreSQL Session pooler connection URI.
   - `AGENT_RUNTIME_ARN`: the ARN of the already deployed AgentCore Runtime.
   - `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: a dedicated AWS IAM
     user's access keys. Never put these in source code or frontend variables.
   - `CORS_ORIGINS`: initially `https://YOUR-PAGES-PROJECT.pages.dev`; replace
     the example with the exact Pages origin after creating the Pages project.
5. Restrict the IAM user's policy to
   `bedrock-agentcore:InvokeAgentRuntime` on this runtime's ARN. The agent
   runtime itself must retain its existing permission to read the Groq key
   from Secrets Manager. Do not copy the Groq key to Render or Cloudflare.
6. Deploy the Blueprint. Copy the API's HTTPS `onrender.com` URL and check
   `https://YOUR-API.onrender.com/` returns the API health message.

Render's Free web service has an ephemeral filesystem. Do not use SQLite for
production there. PostgreSQL is wired through `DATABASE_URL`; Supabase
maintains the database independently from Render service restarts/redeploys.

## Publish the frontend on Cloudflare Pages

1. In Cloudflare, choose **Workers & Pages → Create → Pages → Connect to Git**,
   select the same GitHub repository, and configure:
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Build output directory: `dist`
2. In the Pages project's **Settings → Variables and Secrets → Builds**, add
   `VITE_API_URL` with the full Render API URL, for example
   `https://lauki-faq-api.onrender.com` (no trailing slash).
3. Deploy the Pages project. Copy its production `*.pages.dev` hostname.
4. In Render, update `CORS_ORIGINS` to exactly `https://YOUR-PAGES-PROJECT.pages.dev`
   (or your final custom origin), then redeploy the API.
5. Trigger a new Pages deployment so its production build uses the API URL.
   The production Vite build fails if `VITE_API_URL` is missing, preventing a
   public bundle from silently pointing at localhost.

## Verification

- Open the Pages URL on desktop and a phone-sized viewport.
- Send a question that has an answer in the FAQ.
- Ask a follow-up in the same browser tab and verify the backend uses the
  PostgreSQL-backed session history.
- Refresh the page to verify history restores; use **New chat** for a fresh
  session and **Clear conversation memory** to delete that session's history.
- Check browser network requests use the Render HTTPS API URL and the API
  accepts requests only from the configured CORS origin.

The current chat uses anonymous browser-tab session IDs, not account login.
Anyone can reach the public chat endpoint and can incur LLM/AWS usage. CORS is
not authentication or abuse protection. Monitor provider usage and configure
budget alerts before sharing widely. Free hosting does not make AgentCore or
model-provider inference free.