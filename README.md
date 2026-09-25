# ASATAS Sahi Scan

ASATAS Sahi Scan is a frontend demo for understanding packaged food labels and food-safety signals in an India-focused experience. It explains nutrition against a selected family profile and keeps the reasoning visible.

## Features

- Home page with profile-aware food guidance
- Product scanning simulation with demo products
- Nutrition evaluation against sodium and sugar preferences
- Family profile management
- Ingredient explorer with multilingual explanations
- Better-match alternatives
- Quality reports and report-flow demo
- FSSAI DART loose-food guidance demo
- Sahi-Saath chat with multilingual text and browser-supported voice input/output
- Responsive desktop, tablet, and mobile layouts

## Tech stack

- React 18
- Vite 6
- JavaScript and CSS

## Local setup

```bash
npm install
npm run dev
```

Open the local URL printed by Vite. To preview the production build locally:

```bash
npm run build
npm run preview
```

## Deploy to Vercel

1. Push this project to a Git provider.
2. In Vercel, choose **Add New Project** and import the repository.
3. Keep the detected Vite settings, or use build command `npm run build` and output directory `dist`.
4. Select **Deploy**.

The included `vercel.json` configures the Vite build and routes unknown paths to `index.html` for the client-side app.

## Demo scope

This version is a frontend-only demo. Product, profile, report, and chat data are defined in the frontend. It does not use a backend, database, localhost service, or live product API. Voice features depend on browser support and permissions; unsupported browsers can still use the typed and button-driven flows.
## Image / OCR workflow (Android)

The Android/Capacitor source now supports **Take / upload label photo**. The selected image is sent as multipart form data to `POST /api/v1/scans/image` and the backend performs preprocessing, OCR, QR/2D detection, printed-barcode extraction, nutrition/ingredient parsing, product matching, deterministic profile evaluation, and scan persistence.

For Android Emulator with FastAPI running on the development PC, set the frontend API base to `http://10.0.2.2:8000/api/v1` (a physical phone needs the PC's LAN IP and suitable firewall/CORS configuration).

### Rebuild the Android web assets after changing `src/`

On Windows, from the project root:

```powershell
npm install
npm run build
npx cap copy android
```

Then open/sync the `android/` project in Android Studio and run the app.

The source project is kept alongside the generated Capacitor Android assets so the image workflow is inspectable in VS Code.
