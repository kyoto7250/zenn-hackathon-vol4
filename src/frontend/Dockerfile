# Build stage
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080

# Environment variable substitution is handled automatically by the nginx image 
# when using /etc/nginx/templates/
# But we need to make sure BACKEND_URL is preserved if it was passed as $BACKEND_URL
# The default nginx docker entrypoint handles envsubst for files in /etc/nginx/templates/ ending in .template
# It outputs to /etc/nginx/conf.d/ (removing .template suffix)

CMD ["nginx", "-g", "daemon off;"]
