# see all existing docker images
docker image ls

# build this image
docker build --tag frances-api --label frances-api .

# run this image
docker run frances-api:latest
