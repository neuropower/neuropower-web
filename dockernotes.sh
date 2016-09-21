brew install docker docker-machine docker-compose

docker-machine create --driver virtualbox neuropower
docker-machine create --driver virtualbox

docker-machine start neuropower
eval "$(docker-machine env neuropower)"

docker-compose up -d

#ver loal
exit()
exit
docker-compose restart
docker exec -it ac29eb34477d bash
cd apps/designtoolbox/designcore/
python


docker-compose restart

## install on aws
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -aG docker ec2-user
exit
docker info

# docker compose
sudo -i
curl -L https://github.com/docker/compose/releases/download/1.8.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
exit
docker-compose --version

# git

sudo yum install -y git
git clone https://github.com/neuropower/neuropower-web.git

# docker image
docker pull joke/neuropower:development
docker tag 3099625ea4d5 joke/neuropower:latest

# get secrets
nano /home/ec2-user/neuropower/neuropowertools/secrets.py
mkdir /home/ec2-user/neuropower/media/designonsets
mkdir /home/ec2-user/neuropower/media/designs

6hfvvgxye88pqio45gtug0yyh5qko3c7

docker ps
cd ..
git clone https://github.com/NeuroVault/NeuroVault.git
cd neuropower/
cp ../NeuroVault/Dockerfile .
atom Dockerfile
export ATOM_PATH=/Applications/Atom\ 2.app/
atom Dockerfile
nano Dockerfile
docker build -t filo/neuropower .
cat neuropower/requirements.txt
nano Dockerfile

docker build -t joke/neuropower .
mv Dockerfile neuropower/
docker run -it filo/neuropower python
docker ps

docker ps -a

nano Dockerfile
docker build -t filo/neuropower .
git clean -f
nano docker-compose.yml
docker build -t filo/neuropower .

docker exec -it 649d6f37eb0a bash


scp  -i ~/Documents/Onderzoek/ProjectsOngoing/Neuropower/AWSLinuxinstance.pem ec2-user@ec2-52-53-160-63.us-west-1.compute.amazonaws.com:/home/ec2-user/.ssh/id_rsa ~/Downloads
