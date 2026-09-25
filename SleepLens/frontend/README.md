This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.

---

## SleepLens backend integration

This app is the SleepLens frontend. The complete API integration guide is at
[../docs/FRONTEND_GUIDE.md](../docs/FRONTEND_GUIDE.md):

- auth (JWT cookies/header), response envelope, error codes
- endpoints: patients (full CRUD + per-patient studies), studies (upload/filters/polling),
  /ssc/, /sdi/, /night/, /features/ssc/, /features/sqi/, PSQI, report, signals, download
- drop-in TypeScript types, charts cookbook, honesty rules, limits

Backend dev server: http://127.0.0.1:8000 (Swagger: /api/docs/).
Demo account: demo@sleeplens.local / demopass123 (has a fully processed night + report).
