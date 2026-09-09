# Build the Expo web export, then serve it as static files with nginx.
FROM node:20-slim AS build
WORKDIR /app

ARG EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
ARG EXPO_BASE_URL=
ENV EXPO_PUBLIC_API_BASE_URL=$EXPO_PUBLIC_API_BASE_URL \
    EXPO_BASE_URL=$EXPO_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npx expo export --platform web

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
