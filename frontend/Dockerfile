FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
