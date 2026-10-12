# The web app (Expo web export, PWA) served by nginx -- built from the repo
# root so a platform that clones the repo and builds with the root as context
# (Runflare) needs no extra configuration. Local: docker-compose `frontend`.
FROM node:20-slim AS build
WORKDIR /app

# Baked into the bundle at build time (EXPO_PUBLIC_*), not read at runtime:
# changing the API address means rebuilding the image.
ARG EXPO_PUBLIC_API_BASE_URL=https://api.pharmenta.ir/api/v1
# Served from the domain root, so no sub-path (GitHub Pages uses /Learning_Platform).
ARG EXPO_BASE_URL=
ENV EXPO_PUBLIC_API_BASE_URL=$EXPO_PUBLIC_API_BASE_URL \
    EXPO_BASE_URL=$EXPO_BASE_URL

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npx expo export --platform web

FROM nginx:1.27-alpine
# Size nginx's worker count to this container's CPU quota (cgroup cpu.max)
# instead of the host's core count: on Runflare it otherwise started 16
# workers competing for a fraction of one CPU. Handled by the image's own
# /docker-entrypoint.d/30-tune-worker-processes.sh.
ENV NGINX_ENTRYPOINT_WORKER_PROCESSES_AUTOTUNE=1
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
