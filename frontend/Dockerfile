# ── Stage: dev ────────────────────────────────────────────────────
FROM node:20-alpine AS dev

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host"]

# ── Stage: builder ───────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# ── Stage: prod (nginx) ─────────────────────────────────────────
FROM nginx:alpine AS prod

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
