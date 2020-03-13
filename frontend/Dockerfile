# Use an official node runtime as a parent image
FROM node:10

WORKDIR /app/frontend/

# Install dependencies
COPY package.json yarn.lock /app/frontend/

RUN npm install

# Add rest of the client code
COPY . /app/frontend/

EXPOSE 3000

CMD npm start
