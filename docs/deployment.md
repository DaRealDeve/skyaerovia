# Deploy SkyAerovia on Streamlit Community Cloud

The application is prepared for deployment. The account sign-in, any required terms/access approval and the private API secret must be completed by Tarun (or the key owner privately, without posting the key in chat).

## Open and connect the account

1. Open https://share.streamlit.io and sign in using the GitHub account DaRealDeve.
2. Review and accept Streamlit's terms yourself if prompted.
3. Connect GitHub. The repository DaRealDeve/skyaerovia is private, so Streamlit needs access to it. Review the requested permissions before authorizing; keep the repository private.

## Create the application

4. In the DaRealDeve workspace, choose Create app and deploy an existing GitHub app.
5. Select repository DaRealDeve/skyaerovia, branch main and entry point app.py.
6. Open Advanced settings. Select Python 3.12.
7. In the Secrets box, enter the real key privately using this format:

```toml
GEMINI_API_KEY = "your-working-private-key"
GEMINI_MODEL = "gemini-3.5-flash"
```

Replace the placeholder locally/in the Streamlit form. Do not send the key in a chat or screenshot, or upload secrets.toml to GitHub. Ayman verified this model for his key; verify it for the shared app's key. The model setting can be changed privately if needed.

8. Save the advanced settings and click Deploy. Wait for the app to finish building. The dependencies are pinned to the versions used for local verification.
9. Open the resulting streamlit.app URL and confirm that the logo, welcome message, sidebar and chat input appear.

## Acceptance checks on the hosted app

10. Search Delhi to Mumbai on 2026-10-13. The current committed dataset has three choices: ₹3,200 connecting, ₹3,900 nonstop and ₹4,280 nonstop.
11. Select Nonstop only: two cards should remain. Sort by Shortest duration: the 130-minute flight should appear before the 140-minute flight.
12. Set the sidebar maximum price to ₹3,500 with nonstop enabled: there should be no results. Allow stops: the ₹3,200 choice should appear.
13. Clear chat: the welcome message returns, results disappear and filters reset. Send "from Delhi", then "Mumbai", then "2026-10-13" and confirm the follow-up questions and results.
14. Verify the actual Gemini connection separately with the private key. Chat success alone may be the keyword fallback; the dedicated live check requires source=ai and correct fields. Local command: python scripts/check_gemini.py --live. The existing screenshot proves Ayman's environment, not the shared deployment.

The app also works without a key through the keyword fallback. That is not proof of successful Gemini configuration. A live connection and hosted checks remain pending until performed.

## Later demos

The committed simulated schedule covers 12–18 October 2026. Before a later demo, run python scripts/generate_flights.py in the project folder, check the tests and commit the refreshed data. The cloud app reads the GitHub file; it does not refresh the dates automatically. The app displays its available date range and warns if it expires.

After deployment and final technical checks, prepare Shivam's report, presentation, screenshots and demo recording. All seven members remain in the team; Tarun and Codex cover Yashvardhan's data, Ayush's QA and Shivam's deliverables.

Official references:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account
