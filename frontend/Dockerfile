FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application source code
COPY . .

# Expose Vite server port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev"]
