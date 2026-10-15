FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# FROM nginx:stable-alpine
# COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 3000

#CMD ["nginx", "-g", "daemon off;"]
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]