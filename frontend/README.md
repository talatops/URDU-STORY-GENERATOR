# Urdu Story Generator Frontend

Next.js frontend for the Urdu Children's Story Generation System.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

3. Update `NEXT_PUBLIC_API_URL` in `.env.local` to point to your backend API.

## Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Production

Build for production:
```bash
npm run build
```

Start production server:
```bash
npm start
```

## Deployment

This frontend is designed to be deployed on Vercel. Connect your GitHub repository to Vercel and set the `NEXT_PUBLIC_API_URL` environment variable to your backend API URL.
