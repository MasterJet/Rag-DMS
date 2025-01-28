# Use Node.js for the build process
FROM node:18 as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy application source code
COPY . .

# Build the Next.js app
RUN npm run build

# Use Node.js to serve the application
FROM node:18

# Set working directory
WORKDIR /app

# Copy built files from the previous stage
COPY --from=build /app ./

# Expose port 3000 for Next.js
EXPOSE 3000

# Start the Next.js app
CMD ["npm", "run", "start"]
