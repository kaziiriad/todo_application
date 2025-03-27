# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install bash and gettext for envsubst
RUN apk add --no-cache bash gettext

# Copy the Nginx configuration template
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Copy the entrypoint script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Copy your frontend assets
COPY --from=build /app/dist /usr/share/nginx/html

# Set default environment variable
ENV BACKEND_URL=http://backend:8000
ENV VITE_API_URL=${BACKEND_URL}

EXPOSE 80

# Use the entrypoint script to generate the config and start nginx
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
