# MongoDB Setup

References
https://betterprogramming.pub/persistent-databases-using-dockers-volumes-and-mongodb-9ac284c25b39

To start up the docker image of MongoDB pointing at local file for storage
```
docker run --name mongodb -d -p 27017:27017 -v /Users/dom/OneDrive/Coding/pytracer/data:/data/db mongo
```

# Testing

To run tests use the command from project root directory 
```
python3 -m pytest -v
```