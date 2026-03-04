# Stage 1: build the React app
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install

COPY . .

# Pass the backend URL so the built app points to the right place
ARG VITE_BACKEND_URL=http://localhost:8000
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

RUN npm run build

# Stage 2: serve with nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config: serve index.html for all routes (client-side routing)
RUN echo 'server { \
  listen 80; \
  root /usr/share/nginx/html; \
  index index.html; \
  location / { \
    try_files $uri $uri/ /index.html; \
  } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
