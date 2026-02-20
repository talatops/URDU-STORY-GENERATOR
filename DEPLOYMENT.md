# Deployment Guide: Backend on Render + Frontend on Vercel

This guide explains how to deploy the Urdu Story Generator without Docker Hub, directly from GitHub.

---

## Why Docker Hub Login?

**You don't need Docker Hub for this deployment.**

The GitHub Actions workflow includes an optional Docker Hub login step. It's only needed if you want to:
- **Push** Docker images to Docker Hub for distribution
- **Pull** cached layers from Docker Hub during CI builds

For deploying to **Render**, you skip Docker entirely. Render builds and runs your app directly from the source code—no image registry required.

---

## Can We Deploy Directly to Render?

**Yes.** Render connects to your GitHub repo and deploys automatically on every push. No Docker Hub, no manual image pushes.

---

## Part 1: Deploy Backend to Render

### Prerequisites
- GitHub repo with your code (already done)
- [Render](https://render.com) account (free tier available)

### Step 1: Create a Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub account if not already connected
4. Select the repository: `talatops/URDU-STORY-GENERATOR`
5. Click **Connect**

### Step 2: Configure Backend Settings

| Setting | Value |
|---------|-------|
| **Name** | `urdu-story-backend` (or any name) |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Runtime** | **Python 3** |
| **Build Command** | See below |
| **Start Command** | See below |

### Step 3: Build Command

This installs dependencies and trains the models (creates sample data if none exists):

```bash
pip install -r requirements.txt -r backend/requirements.txt && python data/create_sample_dataset.py && python data/preprocess.py && python train_tokenizer.py && python train_model.py
```

### Step 4: Start Command

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

> **Note:** Render sets `$PORT` automatically. Your app must listen on this port.

### Step 5: Root Directory (Optional)

If Render detects the wrong root, set **Root Directory** to: `.` (project root)

### Step 6: Deploy

1. Click **Create Web Service**
2. Wait for the first build (5–15 minutes; model training takes time)
3. Once deployed, copy your backend URL, e.g. `https://urdu-story-backend.onrender.com`

### Step 7: Free Tier Note

On the free tier, the service **spins down after 15 minutes of inactivity**. The first request after idle may take 30–60 seconds to wake up. For always-on service, use a paid plan.

---

## Part 2: Deploy Frontend to Vercel

### Prerequisites
- [Vercel](https://vercel.com) account (free tier available)

### Step 1: Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import from GitHub: select `talatops/URDU-STORY-GENERATOR`
4. Click **Import**

### Step 2: Configure Frontend Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `.next` (default) |

> **Critical:** You **must** set **Root Directory** to `frontend`. If left empty or set to `.`, Vercel will detect the Python backend and fail with "No fastapi entrypoint found". The backend is deployed separately on Render.

### Step 3: Environment Variable

Add this variable before deploying:

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `https://urdu-story-backend.onrender.com` |

Replace with your actual Render backend URL from Part 1.

> **Important:** `NEXT_PUBLIC_` variables are embedded at build time. If you change the backend URL later, redeploy the frontend.

### Step 4: Deploy

1. Click **Deploy**
2. Wait for the build (1–2 minutes)
3. Your frontend will be live at `https://your-project.vercel.app`

---

## Part 3: Connect Frontend to Backend

### CORS

The backend already allows all origins (`allow_origins=["*"]`). For production, you can restrict this in `backend/main.py`:

```python
allow_origins=[
    "https://your-project.vercel.app",
    "http://localhost:3000"
]
```

### Verify

1. Open your Vercel frontend URL
2. Enter an Urdu prefix (e.g. `ایک`)
3. Click generate—it should call the Render backend and stream the story

---

## Quick Reference

| Component | Platform | URL After Deploy |
|-----------|----------|------------------|
| Backend | Render | `https://urdu-story-backend.onrender.com` |
| Frontend | Vercel | `https://urdu-story-generator.vercel.app` |

---

## Troubleshooting

### Frontend: "No fastapi entrypoint found"
- **Cause:** Vercel is building from the repo root instead of the `frontend` directory, and it detects the Python backend.
- **Fix:** In Vercel Dashboard → Project Settings → General → **Root Directory**, set to `frontend` (not empty, not `.`). Redeploy.

### Backend: "Models not found"
- Ensure the build command runs the full pipeline (create_sample_dataset → preprocess → train_tokenizer → train_model)
- Check Render build logs for errors during model training

### Backend: Build timeout
- Render free tier has a 15-minute build limit. If training is too slow, consider:
  - Committing pre-trained models to the repo (remove `models/*.json` from `.gitignore` for a minimal model)
  - Using a smaller sample in `create_sample_dataset.py`

### Frontend: "API connection failed"
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Ensure the backend URL has no trailing slash
- Redeploy frontend after changing env vars (they are baked in at build time)

### Backend: Cold start on free tier
- First request after 15 min idle can take 30–60 seconds. This is expected on the free tier.
