#!/bin/bash
# Run docker tests on your local machine

PLUGIN_NAME="geogig"

docker rm -f qgis-testing-environment
docker pull elpaso/qgis-testing-environment:latest
docker tag elpaso/qgis-testing-environment:latest qgis-testing-environment

docker run -d  --name qgis-testing-environment  -e DISPLAY=:99 -v /tmp/.X11-unix:/tmp/.X11-unix -v `pwd`:/tests_directory elpaso/qgis-testing-environment:latest

docker exec -it qgis-testing-environment sh -c "qgis_setup.sh $PLUGIN_NAME"

# Extra setup steps
docker exec -it qgis-testing-environment sh -c "apt-get remove -y python-pip && easy_install pip"
docker exec -it qgis-testing-environment sh -c "/usr/local/bin/pip install requests==2.6.0"

docker exec -it qgis-testing-environment sh -c "/usr/local/bin/pip install paver"
docker exec -it qgis-testing-environment sh -c "cd /tests_directory && paver setup"

docker exec -it qgis-testing-environment sh -c "ln -s /tests_directory/$PLUGIN_NAME /root/.qgis2/python/plugins/$PLUGIN_NAME"

#docker exec -it qgis-testing-environment sh -c "qgis_testrunner.sh webappbuilder.tests.layerstest.run_tests"
