FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production image
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
# Install simple http server for serving static files
RUN npm install -g serve

# Run as non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

CMD ["serve", "-s", "dist", "-l", "5173"]
