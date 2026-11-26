# Versión web de MoviContabilidad (la usan los iPhone): Expo la exporta como SPA y nginx la sirve.
# La URL del bot queda fija al construir la imagen (argumento EXPO_PUBLIC_API_URL).

FROM node:24-bookworm-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
ARG EXPO_PUBLIC_API_URL=https://contabilidad.notiasis.com
# EXPO_NO_DOTENV: la URL sale solo del argumento (un .env tendría prioridad sobre él).
ENV CI=1 \
    EXPO_NO_DOTENV=1 \
    EXPO_NO_TELEMETRY=1 \
    EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL}
RUN npx expo export -p web

FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
