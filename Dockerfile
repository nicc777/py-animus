# Dockerfile adopted from the example here: https://stackoverflow.com/questions/48543834/how-do-i-reduce-a-python-docker-image-size-using-a-multi-stage-build
# Credit to https://stackoverflow.com/users/1668328/gcoh

###############################################################################
###                                                                         ###
###                                BASE IMAGE                               ###
###                                                                         ###
###############################################################################
FROM python:3.10-slim as base

RUN apt update && apt -y install python3-dev

RUN mkdir /svc
COPY . /svc
WORKDIR /svc

RUN pip3 install wheel && pip wheel . --wheel-dir=/svc/wheels

###############################################################################
###                                                                         ###
###                               BUILD IMAGE                               ###
###                                                                         ###
###############################################################################
FROM python:3.10-slim as build

COPY --from=base /svc /svc

WORKDIR /svc

RUN pip3 install --no-index --find-links=/svc/wheels -r requirements.txt
RUN pip3 install build
RUN python3 -m build
RUN pip3 uninstall build -y

###############################################################################
###                                                                         ###
###                               FINAL IMAGE                               ###
###                                                                         ###
###############################################################################

FROM python:3.10-slim

RUN mkdir -p /svc/dist
COPY --from=build /svc/dist/* /svc/dist/

WORKDIR /svc

RUN apt update -y && apt install git -y
RUN pip3 install dist/*.tar.gz

ENTRYPOINT [ "animus" ]