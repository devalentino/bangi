FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web/ .
ARG DEBUG_PERSIST_AUTH=false
ENV DEBUG_PERSIST_AUTH=$DEBUG_PERSIST_AUTH
RUN npm run build

FROM nginx:1.27-alpine

COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/index.html /usr/share/nginx/html/index.html
COPY --from=builder /app/app-config.js /usr/share/nginx/html/app-config.js
COPY --from=builder /app/bin /usr/share/nginx/html/bin
COPY --from=builder /app/css /usr/share/nginx/html/css
COPY --from=builder /app/lib /usr/share/nginx/html/lib

EXPOSE 80
