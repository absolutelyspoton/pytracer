# Key Development Highlights

1. Data loaders - File, Restful API, and MongDB ( Local Container and MongoDB Atlas )
2. Implementation of Linear Transforms for a 3D World Coordinate System ( Scale, Rotate, Translate )
3. Use of pydantic module for strict typing / linting and use with FastAPI ( opposed to dataclasses modules )

# MongoDB Setup

References
https://betterprogramming.pub/persistent-databases-using-dockers-volumes-and-mongodb-9ac284c25b39

To start up the docker image of MongoDB pointing at local file for storage
```
docker run --name mongodb -d -p 27017:27017 -v /Users/dom/OneDrive/Coding/pytracer/data:/data/db mongo
```

# FASTAPI setup

To start the server side
```
uvicorn server:app --reload
```

# Testing

To run tests use the command from project root directory 
```
python3 -m pytest -v
```

