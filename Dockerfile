FROM node:18-alpine

WORKDIR /app

# Copy package configurations
COPY package.json ./

# Install npm dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose default port
EXPOSE 8080

# Default command (overridden in compose)
CMD ["node", "web_app/app.js"]
