FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]
