FROM python:3.10-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./missilemap ./server.py ./requirements.txt ./missilemap
COPY ./requirements.txt ./
COPY ./server.py ./

# Install production dependencies.
RUN pip install -r requirements.txt

# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec uvicorn --port $PORT server:app
