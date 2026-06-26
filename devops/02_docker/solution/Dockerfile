FROM node:18-alpine

# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY ../exercise/package*.json ./

RUN npm install

# Bundle app source
COPY ../exercise/server.js ./

EXPOSE 3000
CMD [ "npm", "start" ]
