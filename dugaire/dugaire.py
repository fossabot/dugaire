#!/usr/bin/env python3

""" Import comunity modules. """

import os
import sys
import docker
import click
import jinja2
import uuid
from io import BytesIO

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, f"{HERE}")
sys.path.insert(1, f"{HERE}/../")

""" Import custom modules. """

import setup_info
import util

@click.group()
@click.version_option(setup_info.get_version(), prog_name=setup_info.get_prog_name())
def cli():
  """ CLI tool to build and manage custom Docker images. """
  pass

@cli.command()
@click.option('--from', 'from_', 
  help='Base image (used in Dockerfile FROM). Example: -f=ubuntu',
  metavar='<name:tag>',
  required=True,
  default='ubuntu:18.04',
  show_default=True,
  type=str
)
@click.option('--apt',
  help='Comma separeted list of packages (no blank space) to install using apt-get install. Requires a base image with apt-get. Example: -apt=curl,vim',
  metavar='<pkg01|pkg01,pkg02>',
  required=False
)
@click.option('--pip3',
  help='Comma separeted list of packages (no blank space) to install using pip3 install. WARNING: requires -apt=python3-pip. Example: -apt=python3-pip -pip3=ansible,jinja2',
  metavar='<pkg01|pkg01,pkg02>',
  required=False
)
@click.option('--with-kubectl',
  help="Install kubectl. Examples: --with-kubectl=latest / --with-kubectl=1.17.0",
  metavar='<latest|1.15.0 (or other)>',
  required=False,
)
@click.option('--name',
  help='Image name. Example: --name="myimage:0.0.1"',
  metavar='<name:tag>',
  required=False,
  default='random',
  show_default=True
)
@click.option('--dry-run',
  help='Do not build image.',
  required=False,
  default=False,
  show_default=True,
  is_flag=True
)
@click.option('--output',
  help='Command output options.',
  required=False,
  default='image-id',
  show_default=True,
  type=click.Choice(['image-id', 'image-name', 'dockerfile'], case_sensitive=False)
)
def build(from_, apt, pip3, with_kubectl, name, dry_run, output):
  """
  Build Docker images with custom packages.
  \n
  Examples:
  \n
  Build an image and install vim and curl using apt-get.
  \n
  $ dugaire build --apt=vim,curl
  \n
  Build an image and install python3 using apt-get and ansible using pip3.
  \n
  $ dugaire build --apt=python3-pip --pip3=ansible
  \n
  Build an image and install the latest version of kubectl.
  \n
  $ dugaire build --with-kubectl=latest
  \n

  """
  
  dockerfile = ''

  template = util.get_template('base.j2')
  dockerfile += template.render(from_=from_,label=util.get_dugaire_image_label('dockerfile'))

  if apt:
    packages = apt.replace(',', ' ')
    template = util.get_template('apt.j2')
    dockerfile += template.render(packages=packages)

  if pip3:
    packages = pip3.replace(',', ' ')
    template = util.get_template('pip3.j2')
    dockerfile += template.render(packages=packages)

  if with_kubectl:
    url = 'https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl'
    if with_kubectl != 'latest':
      url = f'https://storage.googleapis.com/kubernetes-release/release/v{with_kubectl}/bin/linux/amd64/kubectl'

    template = util.get_template('with_kubectl.j2')
    dockerfile += template.render(url=url)
  
  image_id = None
  image_name = None
  if not dry_run:
    f = BytesIO(dockerfile.encode('utf-8'))
    client = docker.from_env()
    image_name = name
    if image_name == 'random':
      random_name = str(uuid.uuid4())[:8]
      random_tag = str(uuid.uuid4())[:8]
      image_name = f'dug-{random_name}:{random_tag}'
      
    image, error = client.images.build(
        fileobj=f,
        tag=image_name,
    )
    
    image_id = image.attrs["Id"]
    image_name = image.attrs["RepoTags"][0]
  
  if output == 'image-id':
    click.echo(image_id)
  if output == 'image-name':
    click.echo(image_name)
  if output == 'dockerfile':
    click.echo(dockerfile)

@cli.command("list", help="List images built with dugaire.")
@click.option('--short', '-s',
  help='Print short image ID.',
  required=False,
  default=True,
  show_default=True,
  is_flag=True
)
def list_(short):
  client = docker.from_env()
  images = client.images.list(filters={"label":[util.get_dugaire_image_label()]})
  print_images = []
  for image in images:
    image_id = image.id
    if short:
      image_id = image_id.replace('sha256:', '')[:12]

    image_tag = image.tags

    print_images.append([image_id, image_tag])
  if len(print_images):
    print(util.custom_tabulate(print_images, headers=['Image ID', 'Image tags']))
  else:
    click.echo("No images built with dugaire found.")


def main():
  """ Main function executed by the CLI command. """

  cli()

if __name__ == '__main__':
  """ Call the main function. """
  main()